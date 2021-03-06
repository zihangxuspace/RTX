# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server import util


class ExpertiseLevel(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, description=None, expertise_level_id=None, name=None, score=None, tag=None):  # noqa: E501
        """ExpertiseLevel - a model defined in OpenAPI

        :param description: The description of this ExpertiseLevel.  # noqa: E501
        :type description: str
        :param expertise_level_id: The expertise_level_id of this ExpertiseLevel.  # noqa: E501
        :type expertise_level_id: int
        :param name: The name of this ExpertiseLevel.  # noqa: E501
        :type name: str
        :param score: The score of this ExpertiseLevel.  # noqa: E501
        :type score: float
        :param tag: The tag of this ExpertiseLevel.  # noqa: E501
        :type tag: str
        """
        self.openapi_types = {
            'description': str,
            'expertise_level_id': int,
            'name': str,
            'score': float,
            'tag': str
        }

        self.attribute_map = {
            'description': 'description',
            'expertise_level_id': 'expertise_level_id',
            'name': 'name',
            'score': 'score',
            'tag': 'tag'
        }

        self._description = description
        self._expertise_level_id = expertise_level_id
        self._name = name
        self._score = score
        self._tag = tag

    @classmethod
    def from_dict(cls, dikt) -> 'ExpertiseLevel':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ExpertiseLevel of this ExpertiseLevel.  # noqa: E501
        :rtype: ExpertiseLevel
        """
        return util.deserialize_model(dikt, cls)

    @property
    def description(self):
        """Gets the description of this ExpertiseLevel.


        :return: The description of this ExpertiseLevel.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this ExpertiseLevel.


        :param description: The description of this ExpertiseLevel.
        :type description: str
        """

        self._description = description

    @property
    def expertise_level_id(self):
        """Gets the expertise_level_id of this ExpertiseLevel.


        :return: The expertise_level_id of this ExpertiseLevel.
        :rtype: int
        """
        return self._expertise_level_id

    @expertise_level_id.setter
    def expertise_level_id(self, expertise_level_id):
        """Sets the expertise_level_id of this ExpertiseLevel.


        :param expertise_level_id: The expertise_level_id of this ExpertiseLevel.
        :type expertise_level_id: int
        """

        self._expertise_level_id = expertise_level_id

    @property
    def name(self):
        """Gets the name of this ExpertiseLevel.


        :return: The name of this ExpertiseLevel.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this ExpertiseLevel.


        :param name: The name of this ExpertiseLevel.
        :type name: str
        """

        self._name = name

    @property
    def score(self):
        """Gets the score of this ExpertiseLevel.


        :return: The score of this ExpertiseLevel.
        :rtype: float
        """
        return self._score

    @score.setter
    def score(self, score):
        """Sets the score of this ExpertiseLevel.


        :param score: The score of this ExpertiseLevel.
        :type score: float
        """

        self._score = score

    @property
    def tag(self):
        """Gets the tag of this ExpertiseLevel.


        :return: The tag of this ExpertiseLevel.
        :rtype: str
        """
        return self._tag

    @tag.setter
    def tag(self, tag):
        """Sets the tag of this ExpertiseLevel.


        :param tag: The tag of this ExpertiseLevel.
        :type tag: str
        """

        self._tag = tag
