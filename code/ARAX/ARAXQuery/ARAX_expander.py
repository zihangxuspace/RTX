#!/bin/env python3
import sys
import os

from response import Response
import Expand.expand_utilities as eu

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from swagger_server.models.query_graph import QueryGraph


def eprint(*args, **kwargs): print(*args, file=sys.stderr, **kwargs)


class ARAXExpander:

    def __init__(self):
        self.response = None
        self.message = None
        self.parameters = {'edge_id': None, 'node_id': None, 'kp': None, 'enforce_directionality': None,
                           'use_synonyms': None, 'synonym_handling': None, 'continue_if_no_results': None}

    @staticmethod
    def describe_me():
        """
        Little helper function for internal use that describes the actions and what they can do
        :return:
        """
        # this is quite different than the `describe_me` in ARAX_overlay and ARAX_filter_kg due to expander being less
        # of a dispatcher (like overlay and filter_kg) and more of a single self contained class
        brief_description = """
`expand` effectively takes a query graph (QG) and reaches out to various knowledge providers (KP's) to find all bioentity subgraphs
that satisfy that QG and augments the knowledge graph (KG) with them. As currently implemented, `expand` can utilize the ARA Expander
team KG1 and KG2 Neo4j instances as well as BioThings Explorer to fulfill QG's, with functionality built in to reach out to other KP's as they are rolled out.
        """
        description_list = []
        params_dict = dict()
        params_dict['brief_description'] = brief_description
        params_dict['edge_id'] = {"a query graph edge ID or list of such IDs to expand (optional, default is to expand entire query graph)"}  # this is a workaround due to how self.parameters is utilized in this class
        params_dict['node_id'] = {"a query graph node ID to expand (optional, default is to expand entire query graph)"}
        params_dict['kp'] = {"the knowledge provider to use - current options are `ARAX/KG1`, `ARAX/KG2`, or `BTE` (optional, default is `ARAX/KG1`)"}
        params_dict['enforce_directionality'] = {"whether to obey (vs. ignore) edge directions in query graph - options are `true` or `false` (optional, default is `false`)"}
        params_dict['use_synonyms'] = {"whether to consider synonym curies for query nodes with a curie specified - options are `true` or `false` (optional, default is `true`)"}
        params_dict['synonym_handling'] = {"how to handle synonyms in the answer - options are `map_back` (default; map edges using a synonym back to the original curie) or `add_all` (add synonym nodes as they are - no mapping/merging)"}
        params_dict['continue_if_no_results'] = {"whether to continue execution if no paths are found matching the query graph - options are `true` or `false` (optional, default is `false`)"}
        description_list.append(params_dict)
        return description_list

    def apply(self, input_message, input_parameters, response=None):

        if response is None:
            response = Response()
        self.response = response
        self.message = input_message

        # Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        # Define a complete set of allowed parameters and their defaults
        parameters = self.parameters
        parameters['kp'] = "ARAX/KG1"
        parameters['enforce_directionality'] = False
        parameters['use_synonyms'] = True
        parameters['synonym_handling'] = 'map_back'
        parameters['continue_if_no_results'] = False
        for key,value in input_parameters.items():
            if key and key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                if type(value) is str and value.lower() == "true":
                    value = True
                elif type(value) is str and value.lower() == "false":
                    value = False
                parameters[key] = value

        # Default to expanding the entire query graph if the user didn't specify what to expand
        if not parameters['edge_id'] and not parameters['node_id']:
            parameters['edge_id'] = [edge.id for edge in self.message.query_graph.edges]
            parameters['node_id'] = self._get_orphan_query_node_ids(self.message.query_graph)

        if response.status != 'OK':
            return response

        response.data['parameters'] = parameters
        self.parameters = parameters

        # Do the actual expansion
        response.debug(f"Applying Expand to Message with parameters {parameters}")
        input_edge_ids = eu.convert_string_or_list_to_list(parameters['edge_id'])
        input_node_ids = eu.convert_string_or_list_to_list(parameters['node_id'])
        kp_to_use = self.parameters['kp']
        continue_if_no_results = self.parameters['continue_if_no_results']

        # Convert message knowledge graph to dictionary format, for faster processing
        dict_kg = eu.convert_standard_kg_to_dict_kg(self.message.knowledge_graph)

        # Expand any specified edges
        if input_edge_ids:
            query_sub_graph = self._extract_query_subgraph(input_edge_ids, self.message.query_graph)
            if response.status != 'OK':
                return response
            self.response.debug(f"Query graph for this Expand() call is: {query_sub_graph.to_dict()}")

            # Expand the query graph edge by edge (much faster for neo4j queries, and allows easy integration with BTE)
            ordered_qedges_to_expand = self._get_order_to_expand_edges_in(query_sub_graph)
            node_usages_by_edges_map = dict()

            for qedge in ordered_qedges_to_expand:
                answer_kg, edge_node_usage_map = self._expand_edge(qedge, kp_to_use, dict_kg, continue_if_no_results, self.message.query_graph)
                if response.status != 'OK':
                    return response
                node_usages_by_edges_map[qedge.id] = edge_node_usage_map

                self._process_and_merge_answer(answer_kg, dict_kg)
                if response.status != 'OK':
                    return response

                self._prune_dead_end_paths(dict_kg, query_sub_graph, node_usages_by_edges_map)
                if response.status != 'OK':
                    return response

        # Expand any specified nodes
        if input_node_ids:
            for qnode_id in input_node_ids:
                answer_kg = self._expand_node(qnode_id, kp_to_use, continue_if_no_results, self.message.query_graph)
                if response.status != 'OK':
                    return response

                self._process_and_merge_answer(answer_kg, dict_kg)
                if response.status != 'OK':
                    return response

        # Convert message knowledge graph back to API standard format
        self.message.knowledge_graph = eu.convert_dict_kg_to_standard_kg(dict_kg)

        # Return the response and done
        kg = self.message.knowledge_graph
        response.info(f"After Expand, Message.KnowledgeGraph has {len(kg.nodes)} nodes and {len(kg.edges)} edges")
        return response

    def _extract_query_subgraph(self, qedge_ids_to_expand, query_graph):
        # This function extracts a sub-query graph containing the provided qedge IDs from a larger query graph
        sub_query_graph = QueryGraph(nodes=[], edges=[])

        for qedge_id in qedge_ids_to_expand:
            # Make sure this query edge actually exists in the query graph
            if not any(qedge.id == qedge_id for qedge in query_graph.edges):
                self.response.error(f"An edge with ID '{qedge_id}' does not exist in Message.QueryGraph",
                                    error_code="UnknownValue")
                return sub_query_graph
            qedge = next(qedge for qedge in query_graph.edges if qedge.id == qedge_id)

            # Make sure this qedge's qnodes actually exist in the query graph
            if not eu.get_query_node(query_graph, qedge.source_id):
                self.response.error(f"Qedge {qedge.id}'s source_id refers to a qnode that does not exist in the query "
                                    f"graph: {qedge.source_id}", error_code="InvalidQEdge")
                return sub_query_graph
            if not eu.get_query_node(query_graph, qedge.target_id):
                self.response.error(f"Qedge {qedge.id}'s target_id refers to a qnode that does not exist in the query "
                                    f"graph: {qedge.target_id}", error_code="InvalidQEdge")
                return sub_query_graph
            qnodes = [eu.get_query_node(query_graph, qedge.source_id),
                      eu.get_query_node(query_graph, qedge.target_id)]

            # Add (copies of) this qedge and its two qnodes to our new query sub graph
            qedge_copy = eu.copy_qedge(qedge)
            if not any(qedge.id == qedge_copy.id for qedge in sub_query_graph.edges):
                sub_query_graph.edges.append(qedge_copy)
            for qnode in qnodes:
                qnode_copy = eu.copy_qnode(qnode)
                if not any(qnode.id == qnode_copy.id for qnode in sub_query_graph.nodes):
                    sub_query_graph.nodes.append(qnode_copy)

        return sub_query_graph

    @staticmethod
    def _get_query_graph_for_edge(qedge, query_graph, dict_kg):
        # This function creates a query graph for the specified qedge, updating its qnodes' curies as needed
        edge_query_graph = QueryGraph(nodes=[], edges=[])
        qnodes = [eu.get_query_node(query_graph, qedge.source_id),
                  eu.get_query_node(query_graph, qedge.target_id)]

        # Add (a copy of) this qedge to our edge query graph
        edge_query_graph.edges.append(eu.copy_qedge(qedge))

        # Update this qedge's qnodes as appropriate and add (copies of) them to the edge query graph
        qedge_has_already_been_expanded = qedge.id in dict_kg['edges']
        qnodes_using_curies_from_prior_step = set()
        for qnode in qnodes:
            qnode_copy = eu.copy_qnode(qnode)

            # Handle case where we need to feed curies from a prior Expand() step as the curie for this qnode
            qnode_already_fulfilled = qnode_copy.id in dict_kg['nodes']
            if qnode_already_fulfilled and not qnode_copy.curie and not qedge_has_already_been_expanded:
                qnode_copy.curie = list(dict_kg['nodes'][qnode_copy.id].keys())
                qnodes_using_curies_from_prior_step.add(qnode_copy.id)

            edge_query_graph.nodes.append(qnode_copy)

        return edge_query_graph, qnodes_using_curies_from_prior_step

    def _expand_edge(self, qedge, kp_to_use, dict_kg, continue_if_no_results, query_graph):
        # This function answers a single-edge (one-hop) query using the specified knowledge provider
        self.response.info(f"Expanding edge {qedge.id} using {kp_to_use}")

        edge_query_graph, qnodes_using_curies_from_prior_step = self._get_query_graph_for_edge(qedge, query_graph, dict_kg)
        if not any(qnode for qnode in edge_query_graph.nodes if qnode.curie):
            self.response.error(f"Cannot expand an edge for which neither end has any curies. (Could not find curies to"
                                f" use from a prior expand step, and neither qnode has a curie specified.)",
                                error_code="InvalidQueryGraph")
            return None, None

        valid_kps = ["ARAX/KG1", "ARAX/KG2", "BTE"]
        if kp_to_use not in valid_kps:
            self.response.error(f"Invalid knowledge provider: {kp_to_use}. Valid options are {', '.join(valid_kps)}",
                                error_code="UnknownValue")
            return None, None
        else:
            if kp_to_use == 'BTE':
                from Expand.bte_querier import BTEQuerier
                kp_querier = BTEQuerier(self.response)
            else:
                from Expand.kg_querier import KGQuerier
                kp_querier = KGQuerier(self.response, kp_to_use)

            answer_kg, edge_node_usage_map = kp_querier.answer_one_hop_query(edge_query_graph, qnodes_using_curies_from_prior_step)

            # Make sure all of the QG IDs in our query have been fulfilled (unless we're continuing if no results)
            if self.response.status == 'OK' and not continue_if_no_results:
                for qnode in edge_query_graph.nodes:
                    if qnode.id not in answer_kg['nodes'] or not answer_kg['nodes'][qnode.id]:
                        self.response.error(f"Returned answer KG does not contain any results for QNode {qnode.id}",
                                            error_code="UnfulfilledQGID")
                for qedge in edge_query_graph.edges:
                    if qedge.id not in answer_kg['edges'] or not answer_kg['edges'][qedge.id]:
                        self.response.error(f"Returned answer KG does not contain any results for QEdge {qedge.id}",
                                            error_code="UnfulfilledQGID")

            return answer_kg, edge_node_usage_map

    def _expand_node(self, qnode_id, kp_to_use, continue_if_no_results, query_graph):
        # This function expands a single node using the specified knowledge provider
        self.response.debug(f"Expanding node {qnode_id} using {kp_to_use}")

        query_node = eu.get_query_node(query_graph, qnode_id)
        if self.response.status != 'OK':
            return None

        if kp_to_use == 'BTE':
            self.response.error(f"Cannot use BTE to answer single node queries", error_code="InvalidQuery")
            return None
        elif kp_to_use == 'ARAX/KG2' or kp_to_use == 'ARAX/KG1':
            from Expand.kg_querier import KGQuerier
            kg_querier = KGQuerier(self.response, kp_to_use)
            answer_kg = kg_querier.answer_single_node_query(query_node)

            # Make sure all qnodes have been fulfilled (unless we're continuing if no results)
            if self.response.status == 'OK' and not continue_if_no_results:
                if query_node.id not in answer_kg['nodes'] or not answer_kg['nodes'][query_node.id]:
                    self.response.error(f"Returned answer KG does not contain any results for QNode {query_node.id}",
                                        error_code="UnfulfilledQGID")
            return answer_kg
        else:
            self.response.error(f"Invalid knowledge provider: {kp_to_use}. Valid options are ARAX/KG1 or ARAX/KG2")
            return None

    def _process_and_merge_answer(self, answer_dict_kg, dict_kg):
        # This function merges an answer KG (from the current edge/node expansion) into the overarching KG
        self.response.debug("Merging answer into Message.KnowledgeGraph")

        for qnode_id, nodes in answer_dict_kg['nodes'].items():
            for node_key, node in nodes.items():
                eu.add_node_to_kg(dict_kg, node, qnode_id)
        for qedge_id, edges_dict in answer_dict_kg['edges'].items():
            for edge_key, edge in edges_dict.items():
                eu.add_edge_to_kg(dict_kg, edge, qedge_id)

    def _prune_dead_end_paths(self, dict_kg, full_query_graph, node_usages_by_edges_map):
        # This function removes any 'dead-end' paths from the KG. (Because edges are expanded one-by-one, not all edges
        # found in the last expansion will connect to edges in the next one)
        self.response.debug(f"Pruning any paths that are now dead ends")

        # Create a map of which qnodes are connected to which other qnodes
        # Example qnode_connections_map: {'n00': {'n01'}, 'n01': {'n00', 'n02'}, 'n02': {'n01'}}
        qnode_connections_map = dict()
        for qnode in full_query_graph.nodes:
            qnode_connections_map[qnode.id] = set()
            for qedge in full_query_graph.edges:
                if qedge.source_id == qnode.id or qedge.target_id == qnode.id:
                    connected_qnode_id = qedge.target_id if qedge.target_id != qnode.id else qedge.source_id
                    qnode_connections_map[qnode.id].add(connected_qnode_id)

        # Create a map of which nodes each node is connected to (organized by the qnode_id they're fulfilling)
        # Example node_usages_by_edges_map: {'e00': {'KG1:111221': {'n00': 'CUI:122', 'n01': 'CUI:124'}}}
        # Example node_connections_map: {'CUI:1222': {'n00': {'DOID:122'}, 'n02': {'UniProtKB:22', 'UniProtKB:333'}}}
        node_connections_map = dict()
        for qedge_id, edges_to_nodes_dict in node_usages_by_edges_map.items():
            current_qedge = next(qedge for qedge in full_query_graph.edges if qedge.id == qedge_id)
            qnode_ids = [current_qedge.source_id, current_qedge.target_id]
            for edge_id, node_usages_dict in edges_to_nodes_dict.items():
                for current_qnode_id in qnode_ids:
                    connected_qnode_id = next(qnode_id for qnode_id in qnode_ids if qnode_id != current_qnode_id)
                    current_node_id = node_usages_dict[current_qnode_id]
                    connected_node_id = node_usages_dict[connected_qnode_id]
                    if current_qnode_id not in node_connections_map:
                        node_connections_map[current_qnode_id] = dict()
                    if current_node_id not in node_connections_map[current_qnode_id]:
                        node_connections_map[current_qnode_id][current_node_id] = dict()
                    if connected_qnode_id not in node_connections_map[current_qnode_id][current_node_id]:
                        node_connections_map[current_qnode_id][current_node_id][connected_qnode_id] = set()
                    node_connections_map[current_qnode_id][current_node_id][connected_qnode_id].add(connected_node_id)

        # Iteratively remove all disconnected nodes until there are none left
        qnode_ids_already_expanded = list(node_connections_map.keys())
        found_dead_end = True
        while found_dead_end:
            found_dead_end = False
            for qnode_id in qnode_ids_already_expanded:
                qnode_ids_should_be_connected_to = qnode_connections_map[qnode_id].intersection(qnode_ids_already_expanded)
                for node_id, node_mappings_dict in node_connections_map[qnode_id].items():
                    # Check if any mappings are even entered for all qnode_ids this node should be connected to
                    if set(node_mappings_dict.keys()) != qnode_ids_should_be_connected_to:
                        if node_id in dict_kg['nodes'][qnode_id]:
                            dict_kg['nodes'][qnode_id].pop(node_id)
                            found_dead_end = True
                    else:
                        # Verify that at least one of the entered connections still exists (for each connected qnode_id)
                        for connected_qnode_id, connected_node_ids in node_mappings_dict.items():
                            if not connected_node_ids.intersection(set(dict_kg['nodes'][connected_qnode_id].keys())):
                                if node_id in dict_kg['nodes'][qnode_id]:
                                    dict_kg['nodes'][qnode_id].pop(node_id)
                                    found_dead_end = True

        # Then remove all orphaned edges
        for qedge_id, edges_dict in node_usages_by_edges_map.items():
            for edge_key, node_mappings in edges_dict.items():
                for qnode_id, used_node_id in node_mappings.items():
                    if used_node_id not in dict_kg['nodes'][qnode_id]:
                        if edge_key in dict_kg['edges'][qedge_id]:
                            dict_kg['edges'][qedge_id].pop(edge_key)

    def _get_order_to_expand_edges_in(self, query_graph):
        # This function determines what order to expand the edges in a query graph in; it attempts to start with
        # qedges that have a qnode with a specific curie, and move out from there.
        edges_remaining = [edge for edge in query_graph.edges]
        ordered_edges = []
        while edges_remaining:
            if not ordered_edges:
                # Start with an edge that has a node with a curie specified
                edge_with_curie = self._get_edge_with_curie_node(query_graph)
                first_edge = edge_with_curie if edge_with_curie else edges_remaining[0]
                ordered_edges = [first_edge]
                edges_remaining.pop(edges_remaining.index(first_edge))
            else:
                # Add connected edges in a rightward (target) direction if possible
                right_end_edge = ordered_edges[-1]
                edge_connected_to_right_end = self._find_connected_edge(edges_remaining, right_end_edge)
                if edge_connected_to_right_end:
                    ordered_edges.append(edge_connected_to_right_end)
                    edges_remaining.pop(edges_remaining.index(edge_connected_to_right_end))
                else:
                    left_end_edge = ordered_edges[0]
                    edge_connected_to_left_end = self._find_connected_edge(edges_remaining, left_end_edge)
                    if edge_connected_to_left_end:
                        ordered_edges.insert(0, edge_connected_to_left_end)
                        edges_remaining.pop(edges_remaining.index(edge_connected_to_left_end))
        return ordered_edges

    @staticmethod
    def _get_orphan_query_node_ids(query_graph):
        node_ids_used_by_edges = set()
        node_ids = set()
        for edge in query_graph.edges:
            node_ids_used_by_edges.add(edge.source_id)
            node_ids_used_by_edges.add(edge.target_id)
        for node in query_graph.nodes:
            node_ids.add(node.id)
        return list(node_ids.difference(node_ids_used_by_edges))

    @staticmethod
    def _get_edge_with_curie_node(query_graph):
        for edge in query_graph.edges:
            source_node = eu.get_query_node(query_graph, edge.source_id)
            target_node = eu.get_query_node(query_graph, edge.target_id)
            if source_node.curie or target_node.curie:
                return edge
        return None

    @staticmethod
    def _find_connected_edge(edge_list, edge):
        edge_node_ids = {edge.source_id, edge.target_id}
        for potential_connected_edge in edge_list:
            potential_connected_edge_node_ids = {potential_connected_edge.source_id, potential_connected_edge.target_id}
            if edge_node_ids.intersection(potential_connected_edge_node_ids):
                return potential_connected_edge
        return None


def main():

    # Note that most of this is just manually doing what ARAXQuery() would normally do for you
    response = Response()
    from actions_parser import ActionsParser
    actions_parser = ActionsParser()
    actions_list = [
        "create_message",
        "add_qnode(id=n00, curie=CHEMBL.COMPOUND:CHEMBL112)",  # acetaminophen
        "add_qnode(id=n01, type=protein, is_set=true)",
        "add_qedge(id=e00, source_id=n00, target_id=n01)",
        "expand(edge_id=e00, kp=BTE)",
        "return(message=true, store=false)",
    ]

    # Parse the raw action_list into commands and parameters
    result = actions_parser.parse(actions_list)
    response.merge(result)
    if result.status != 'OK':
        print(response.show(level=Response.DEBUG))
        return response
    actions = result.data['actions']

    from ARAX_messenger import ARAXMessenger
    messenger = ARAXMessenger()
    expander = ARAXExpander()
    for action in actions:
        if action['command'] == 'create_message':
            result = messenger.create_message()
            message = result.data['message']
            response.data = result.data
        elif action['command'] == 'add_qnode':
            result = messenger.add_qnode(message,action['parameters'])
        elif action['command'] == 'add_qedge':
            result = messenger.add_qedge(message,action['parameters'])
        elif action['command'] == 'expand':
            result = expander.apply(message,action['parameters'])
        elif action['command'] == 'return':
            break
        else:
            response.error(f"Unrecognized command {action['command']}", error_code="UnrecognizedCommand")
            print(response.show(level=Response.DEBUG))
            return response

        # Merge down this result and end if we're in an error state
        response.merge(result)
        if result.status != 'OK':
            print(response.show(level=Response.DEBUG))
            return response

    # Show the final response
    # print(json.dumps(ast.literal_eval(repr(message.knowledge_graph)),sort_keys=True,indent=2))
    print(response.show(level=Response.DEBUG))


if __name__ == "__main__":
    main()
