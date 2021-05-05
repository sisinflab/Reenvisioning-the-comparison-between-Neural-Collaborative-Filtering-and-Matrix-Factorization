"""
Module description:

"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import numpy as np
import pickle

from elliot.recommender.recommender_utils_mixin import RecMixin
from elliot.utils.write import store_recommendation
from .iALS_model import iALSModel
from elliot.recommender.base_recommender_model import BaseRecommenderModel
from elliot.recommender.base_recommender_model import init_charger

np.random.seed(42)


class iALS(RecMixin, BaseRecommenderModel):
    r"""
    Weighted XXX Matrix Factorization

    For further details, please refer to the `paper <https://archive.siam.org/meetings/sdm06/proceedings/059zhangs2.pdf>`_

    Args:
        factors: Number of latent factors
        lr: Learning rate
        alpha:
        reg: Regularization coefficient

    To include the recommendation model, add it to the config file adopting the following pattern:

    .. code:: yaml

      models:
        WRMF:
          meta:
            save_recs: True
          epochs: 10
          factors: 50
          alpha: 1
          reg: 0.1
    """

    @init_charger
    def __init__(self, data, config, params, *args, **kwargs):
        self._random = np.random

        self._params_list = [
            ("_factors", "factors", "factors", 10, int, None),
            ("_alpha", "alpha", "alpha", 1, float, None),
            ("_epsilon", "epsilon", "epsilon", 1, float, None),
            ("_reg", "reg", "reg", 0.1, float, None),
            ("_scaling", "scaling", "scaling", "linear", None, None)
        ]
        self.autoset_params()

        self._ratings = self._data.train_dict
        self._sp_i_train = self._data.sp_i_train

        self._model = iALSModel(self._factors, self._data, self._random, self._alpha, self._epsilon, self._reg,
                                self._scaling)

    # def get_recommendations(self, k: int = 100):
    #     return {u: self._model.get_user_recs(u, k) for u in self._ratings.keys()}

    def get_recommendations(self, k: int = 10):
        self._model.prepare_predictions()

        predictions_top_k_val = {}
        predictions_top_k_test = {}

        recs_val, recs_test = self.process_protocol(k)

        predictions_top_k_val.update(recs_val)
        predictions_top_k_test.update(recs_test)

        return predictions_top_k_val, predictions_top_k_test

    def get_single_recommendation(self, mask, k, *args):
        return {u: self._model.get_user_recs(u, mask, k) for u in self._data.train_dict.keys()}

    # def predict(self, u: int, i: int):
    #     """
    #     Get prediction on the user item pair.
    #
    #     Returns:
    #         A single float vaue.
    #     """
    #     return self._model.predict(u, i)

    @property
    def name(self):
        return "WRMF" \
               + "_e:" + str(self._epochs) \
               + f"_{self.get_params_shortcut()}"

    def train(self):
        if self._restore:
            return self.restore_weights()

        best_metric_value = 0
        for it in range(self._epochs):
            self._model.train_step()

            print("Iteration Finished")

            self.evaluate(it)

            # if not (it + 1) % self._validation_rate:
            #     recs = self.get_recommendations(self.evaluator.get_needed_recommendations())
            #     result_dict = self.evaluator.eval(recs)
            #     self._results.append(result_dict)
            #
            #     print(f'Epoch {(it + 1)}/{self._epochs}')
            #
            #     if self._results[-1][self._validation_k]["val_results"][self._validation_metric] > best_metric_value:
            #         print("******************************************")
            #         best_metric_value = self._results[-1][self._validation_k]["val_results"][self._validation_metric]
            #         if self._save_weights:
            #             with open(self._saving_filepath, "wb") as f:
            #                 pickle.dump(self._model.get_model_state(), f)
            #         if self._save_recs:
            #             store_recommendation(recs, self._config.path_output_rec_result + f"{self.name}-it:{it + 1}.tsv")

    def restore_weights(self):
        try:
            with open(self._saving_filepath, "rb") as f:
                self._model.set_model_state(pickle.load(f))
            print(f"Model correctly Restored")

            recs = self.get_recommendations(self.evaluator.get_needed_recommendations())
            result_dict = self.evaluator.eval(recs)
            self._results.append(result_dict)

            print("******************************************")
            if self._save_recs:
                store_recommendation(recs, self._config.path_output_rec_result + f"{self.name}.tsv")
            return True

        except Exception as ex:
            print(f"Error in model restoring operation! {ex}")

        return False
