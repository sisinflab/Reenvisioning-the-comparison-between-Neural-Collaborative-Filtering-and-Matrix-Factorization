"""
This is the implementation of the Expected Free Discovery metric.
It proceeds from a user-wise computation, and average the values over the users.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import math
import numpy as np
from elliot.evaluation.metrics.base_metric import BaseMetric


class EFD(BaseMetric):
    r"""
    Expected Free Discovery (EFD)

    This class represents the implementation of the Expected Free Discovery recommendation metric.

    For further details, please refer to the `paper <https://dl.acm.org/doi/pdf/10.1145/2043932.2043955>`_

    Note:
         EFD can be read as the expected ICF of seen recommended items

    .. math::
       \mathrm {EFD}=C \sum_{i_{k} \in R} {disc}(k) p({rel} \mid i_{k}, u)( -\log _{2} p(i \mid {seen}, \theta))

    To compute the metric, add it to the config file adopting the following pattern:

    .. code:: yaml

        simple_metrics: [EFD]
    """

    def __init__(self, recommendations, config, params, eval_objects):
        """
        Constructor
        :param recommendations: list of recommendations in the form {user: [(item1,value1),...]}
        :param config: SimpleNameSpace that represents the configuration of the experiment
        :param params: Parameters of the model
        :param eval_objects: list of objects that may be useful for the computation of the different metrics
        """
        super().__init__(recommendations, config, params, eval_objects)
        self._cutoff = self._evaluation_objects.cutoff
        self._relevance = self._evaluation_objects.relevance.binary_relevance

    @staticmethod
    def name():
        """
        Metric Name Getter
        :return: returns the public name of the metric
        """
        return "EFD"

    def __user_EFD(self, user_recommendations, user, cutoff):
        """
        Per User Expected Free Discovery
        :param user_recommendations: list of user recommendation in the form [(item1,value1),...]
        :param cutoff: numerical threshold to limit the recommendation list
        :param user_relevant_items: list of user relevant items in the form [item1,...]
        :return: the value of the Precision metric for the specific user
        """

        nov = 0
        norm = 0
        for r, (i, _) in enumerate(user_recommendations[:cutoff]):
            nov += self._relevance.get_rel(user, i) * self._relevance.logarithmic_ranking_discount(r) * self._item_novelty_dict.get(i, self._max_nov)
            norm += self._relevance.logarithmic_ranking_discount(r)

        if norm > 0:
            nov /= norm

        return nov

    # @staticmethod
    # def __discount_k(k):
    #     return (1 / math.log(k + 2)) * math.log(2)

    # def eval(self):
    #     """
    #     Evaluation function
    #     :return: the overall averaged value of Expected Free Discovery
    #     """
    #
    #     self._item_count = {}
    #     for u_h in self._evaluation_objects.data.train_dict.values():
    #         for i in u_h.keys():
    #             self._item_count[i] = self._item_count.get(i, 0) + 1
    #
    #     novelty_profile = self._item_count.values()
    #     norm = sum(novelty_profile)
    #     self._max_nov = -math.log(min(novelty_profile) / norm) / math.log(2)
    #     self._item_novelty_dict = {i: -math.log(v / norm) / math.log(2) for i, v in self._item_count.items()}
    #
    #     return np.average([self.__user_EFD(u_r, self._cutoff, self._relevant_items[u])
    #          for u, u_r in self._recommendations.items() if len(self._relevant_items[u])])

    def eval_user_metric(self):
        """
        Evaluation function
        :return: the overall averaged value of Expected Free Discovery per user
        """

        self._item_count = {}
        for u_h in self._evaluation_objects.data.train_dict.values():
            for i in u_h.keys():
                self._item_count[i] = self._item_count.get(i, 0) + 1

        novelty_profile = self._item_count.values()
        norm = sum(novelty_profile)
        self._max_nov = -math.log(min(novelty_profile) / norm) / math.log(2)
        self._item_novelty_dict = {i: -math.log(v / norm) / math.log(2) for i, v in self._item_count.items()}

        return {u: self.__user_EFD(u_r, u, self._cutoff)
                for u, u_r in self._recommendations.items() if len(self._relevance.get_user_rel(u))}

