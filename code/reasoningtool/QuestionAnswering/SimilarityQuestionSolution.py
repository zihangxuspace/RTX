# This script will return X that are similar to Y based on high Jaccard index of common one-hop nodes Z (X<->Z<->Y)

import os
import sys
import argparse
# PyCharm doesn't play well with relative imports + python console + terminal
try:
	from code.reasoningtool import ReasoningUtilities as RU
except ImportError:
	sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	import ReasoningUtilities as RU

#### Import some Translator API classes
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from swagger_server.models.query_graph import QueryGraph
from swagger_server.models.q_node import QNode
from swagger_server.models.q_edge import QEdge

import FormatOutput

import SimilarNodesInCommon
import networkx as nx


class SimilarityQuestionSolution:

	def __init__(self):
		None

	@staticmethod
	def answer(source_node_ID, target_node_type, association_node_type, use_json=False, threshold=0.2, n=20):
		"""
		Answers the question what X are similar to Y based on overlap of common Z nodes. X is target_node_type,
		Y is source_node_ID, Z is association_node_type. The relationships are automatically determined in
		SimilarNodesInCommon by looking for 1 hop relationships and poping the FIRST one (you are warned).
		:param source_node_ID: actual name in the KG
		:param target_node_type: kinds of nodes you want returned
		:param association_node_type: kind of node you are computing the Jaccard overlap on
		:param use_json: print the results in standardized format
		:param threshold: only return results where jaccard is >= this threshold
		:param n: number of results to return (default 20)
		:return: reponse (or printed text)
		"""

		# Initialize the response class
		response = FormatOutput.FormatResponse(5)
		# add the column names for the row data
		response.message.table_column_names = ["source name", "source ID", "target name", "target ID", "Jaccard index"]

		# Initialize the similar nodes class
		similar_nodes_in_common = SimilarNodesInCommon.SimilarNodesInCommon()

		# get the description
		source_node_description = RU.get_node_property(source_node_ID, 'name')

		# get the source node label
		source_node_label = RU.get_node_property(source_node_ID, 'label')

		# Get the nodes in common
		node_jaccard_tuples_sorted, error_code, error_message = similar_nodes_in_common.get_similar_nodes_in_common_source_target_association(source_node_ID, target_node_type, association_node_type, threshold)

		# reduce to top 100
		if len(node_jaccard_tuples_sorted) > n:
			node_jaccard_tuples_sorted = node_jaccard_tuples_sorted[0:n]

		# make sure that the input node isn't in the list
		node_jaccard_tuples_sorted = [i for i in node_jaccard_tuples_sorted if i[0] != source_node_ID]

		# check for an error
		if error_code is not None or error_message is not None:
			if not use_json:
				print(error_message)
				return
			else:
				response.add_error_message(error_code, error_message)
				response.print()
				return

		#### If use_json not specified, then return results as a fairly plain list
		if not use_json:
			to_print = "The %s's involving similar %ss as %s are: \n" % (target_node_type, association_node_type, source_node_description)
			for other_disease_ID, jaccard in node_jaccard_tuples_sorted:
				to_print += "%s\t%s\tJaccard %f\n" % (other_disease_ID, RU.get_node_property(other_disease_ID, 'name'), jaccard)
			print(to_print)

		#### Else if use_json requested, return the results in the Translator standard API JSON format
		else:

			#### Create the QueryGraph for this type of question
			query_graph = QueryGraph()
			source_node = QNode()
			source_node.node_id = "n00"
			source_node.curie = source_node_ID
			source_node.type = source_node_label
			association_node = QNode()
			association_node.node_id = "n01"
			association_node.type = association_node_type
			association_node.is_set = True
			target_node = QNode()
			target_node.node_id = "n02"
			target_node.type = target_node_type
			query_graph.nodes = [ source_node,association_node,target_node ]

			source_association_relationship_type = "unknown1"
			edge1 = QEdge()
			edge1.edge_id = "en00-n01"
			edge1.source_id = "n00"
			edge1.target_id = "n01"
			edge1.type = source_association_relationship_type

			association_target_relationship_type = "unknown2"
			edge2 = QEdge()
			edge2.edge_id = "en01-n02"
			edge2.source_id = "n01"
			edge2.target_id = "n02"
			edge2.type = association_target_relationship_type

			query_graph.edges = [ edge1,edge2 ]

			#### DONT Suppress the query_graph because we can now do the knowledge_map with v0.9.1
			response.message.query_graph = query_graph

			#### Create a mapping dict with the source curie and node types and edge types. This dict is used for reverse lookups by type
			#### for mapping to the QueryGraph. There is a potential point of failure here if there are duplicate node or edge types. FIXME
			response._type_map = dict()
			response._type_map[source_node.curie] = source_node.node_id
			response._type_map[association_node.type] = association_node.node_id
			response._type_map[target_node.type] = target_node.node_id
			response._type_map["e"+edge1.source_id+"-"+edge1.target_id] = edge1.edge_id
			response._type_map["e"+edge2.source_id+"-"+edge2.target_id] = edge2.edge_id

			#### Extract the sorted IDs from the list of tuples
			node_jaccard_ID_sorted = [id for id, jac in node_jaccard_tuples_sorted]

			# print(RU.return_subgraph_through_node_labels(source_node_ID, source_node_label, node_jaccard_ID_sorted, target_node_type,
			#										[association_node_type], with_rel=[], directed=True, debug=True))

			# get the entire subgraph
			g = RU.return_subgraph_through_node_labels(source_node_ID, source_node_label, node_jaccard_ID_sorted,
													target_node_type,
													[association_node_type], with_rel=[], directed=False,
													debug=False)

			# extract the source_node_number
			for node, data in g.nodes(data=True):
				if data['properties']['id'] == source_node_ID:
					source_node_number = node
					break

			# Get all the target numbers
			target_id2numbers = dict()
			node_jaccard_ID_sorted_set = set(node_jaccard_ID_sorted)
			for node, data in g.nodes(data=True):
				if data['properties']['id'] in node_jaccard_ID_sorted_set:
					target_id2numbers[data['properties']['id']] = node

			for other_disease_ID, jaccard in node_jaccard_tuples_sorted:
				target_name = RU.get_node_property(other_disease_ID, 'name')
				to_print = "The %s %s involves similar %ss as %s with similarity value %f" % (
					target_node_type, target_name, association_node_type,
					source_node_description, jaccard)

				# get all the shortest paths between source and target
				all_paths = nx.all_shortest_paths(g, source_node_number, target_id2numbers[other_disease_ID])

				# get all the nodes on these paths
				#try:
				if 1 == 1:
					rel_nodes = set()
					for path in all_paths:
						for node in path:
							rel_nodes.add(node)

					if rel_nodes:
						# extract the relevant subgraph
						sub_g = nx.subgraph(g, rel_nodes)

						# add it to the response
						res = response.add_subgraph(sub_g.nodes(data=True), sub_g.edges(data=True), to_print, jaccard, return_result=True)
						res.essence = "%s" % target_name  # populate with essence of question result
						res.essence_type = target_node_type
						row_data = []  # initialize the row data
						row_data.append("%s" % source_node_description)
						row_data.append("%s" % source_node_ID)
						row_data.append("%s" % target_name)
						row_data.append("%s" % other_disease_ID)
						row_data.append("%f" % jaccard)
						res.row_data = row_data
#				except:
#					pass
			response.print()

	@staticmethod
	def describe():
		output = "Answers questions of the form: 'What diseases involve similar genes to disease X?' where X is a disease." + "\n"
		# TODO: subsample disease nodes
		return output


def main():
	parser = argparse.ArgumentParser(description="Answers questions of the type 'What X involve similar Y as Z?'.",
									formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-s', '--source', type=str, help="source node name (or other name of node in the KG)", default="DOID:8398")
	parser.add_argument('-t', '--target', type=str, help="target node type", default="disease")
	parser.add_argument('-a', '--association', type=str, help="association node type", default="phenotypic_feature")
	parser.add_argument('-j', '--json', action='store_true', help='Flag specifying that results should be printed in JSON format (to stdout)', default=False)
	parser.add_argument('--describe', action='store_true', help='Print a description of the question to stdout and quit', default=False)
	parser.add_argument('--threshold', type=float, help='Jaccard index threshold (only report other diseases above this)', default=0.2)
	parser.add_argument('-n', '--num_res', type=int, help='Maximum number of results to return', default=20)

	# Parse and check args
	args = parser.parse_args()
	source_node_ID = args.source
	use_json = args.json
	describe_flag = args.describe
	threshold = args.threshold
	target_node_type = args.target
	association_node_type = args.association
	n = args.num_res

	# Initialize the question class
	Q = SimilarityQuestionSolution()

	if describe_flag:
		res = Q.describe()
		print(res)
	else:
		Q.answer(source_node_ID, target_node_type, association_node_type, use_json=use_json, threshold=threshold, n=n)


if __name__ == "__main__":
	main()
