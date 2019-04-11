# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class QNode(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, node_id: str=None, curie: str=None, type: str=None, is_set: bool=None):  # noqa: E501
        """QNode - a model defined in Swagger

        :param node_id: The node_id of this QNode.  # noqa: E501
        :type node_id: str
        :param curie: The curie of this QNode.  # noqa: E501
        :type curie: str
        :param type: The type of this QNode.  # noqa: E501
        :type type: str
        :param is_set: The is_set of this QNode.  # noqa: E501
        :type is_set: bool
        """
        self.swagger_types = {
            'node_id': str,
            'curie': str,
            'type': str,
            'is_set': bool
        }

        self.attribute_map = {
            'node_id': 'node_id',
            'curie': 'curie',
            'type': 'type',
            'is_set': 'is_set'
        }

        self._node_id = node_id
        self._curie = curie
        self._type = type
        self._is_set = is_set

    @classmethod
    def from_dict(cls, dikt) -> 'QNode':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The QNode of this QNode.  # noqa: E501
        :rtype: QNode
        """
        return util.deserialize_model(dikt, cls)

    @property
    def node_id(self) -> str:
        """Gets the node_id of this QNode.

        QueryGraph internal identifier for this QNode. Recommended form: n00, n01, n02, etc.  # noqa: E501

        :return: The node_id of this QNode.
        :rtype: str
        """
        return self._node_id

    @node_id.setter
    def node_id(self, node_id: str):
        """Sets the node_id of this QNode.

        QueryGraph internal identifier for this QNode. Recommended form: n00, n01, n02, etc.  # noqa: E501

        :param node_id: The node_id of this QNode.
        :type node_id: str
        """

        self._node_id = node_id

    @property
    def curie(self) -> str:
        """Gets the curie of this QNode.

        CURIE identifier for this node  # noqa: E501

        :return: The curie of this QNode.
        :rtype: str
        """
        return self._curie

    @curie.setter
    def curie(self, curie: str):
        """Sets the curie of this QNode.

        CURIE identifier for this node  # noqa: E501

        :param curie: The curie of this QNode.
        :type curie: str
        """

        self._curie = curie

    @property
    def type(self) -> str:
        """Gets the type of this QNode.

        Entity type of this node (e.g., protein, disease, etc.)  # noqa: E501

        :return: The type of this QNode.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this QNode.

        Entity type of this node (e.g., protein, disease, etc.)  # noqa: E501

        :param type: The type of this QNode.
        :type type: str
        """

        self._type = type

    @property
    def is_set(self) -> bool:
        """Gets the is_set of this QNode.

        If set, this node represents a set of nodes  # noqa: E501

        :return: The is_set of this QNode.
        :rtype: bool
        """
        return self._is_set

    @is_set.setter
    def is_set(self, is_set: bool):
        """Sets the is_set of this QNode.

        If set, this node represents a set of nodes  # noqa: E501

        :param is_set: The is_set of this QNode.
        :type is_set: bool
        """

        self._is_set = is_set