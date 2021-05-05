"""
Module description:

"""


__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

import numpy as np
from ast import literal_eval as make_tuple
from tqdm import tqdm

from elliot.dataset.samplers import pointwise_pos_neg_ratio_ratings_sampler as pws
from elliot.recommender.neural.DMF.deep_matrix_factorization_model import DeepMatrixFactorizationModel
from elliot.recommender.recommender_utils_mixin import RecMixin
from elliot.utils.write import store_recommendation
from elliot.recommender.base_recommender_model import BaseRecommenderModel
from elliot.recommender.base_recommender_model import init_charger

np.random.seed(42)


class DMF(RecMixin, BaseRecommenderModel):
    r"""
        Deep Matrix Factorization Models for Recommender Systems.

        For further details, please refer to the `paper <https://www.ijcai.org/Proceedings/2017/0447.pdf>`_

        Args:
            lr: Learning rate
            reg: Regularization coefficient
            user_mlp: List of units for each layer
            item_mlp: List of activation functions
            similarity: Number of factors dimension


        To include the recommendation model, add it to the config file adopting the following pattern:

        .. code:: yaml

          models:
            DMF:
              meta:
                save_recs: True
              epochs: 10
              batch_size: 512
              lr: 0.0001
              reg: 0.001
              user_mlp: (64,32)
              item_mlp: (64,32)
              similarity: cosine
        """
    @init_charger
    def __init__(self, data, config, params, *args, **kwargs):
        self._random = np.random

        self._params_list = [
            ("_learning_rate", "lr", "lr", 0.0001, None, None),
            ("_user_mlp", "user_mlp", "umlp", "(64,32)", lambda x: list(make_tuple(str(x))), lambda x: self._batch_remove(str(x), " []").replace(",", "-")),
            ("_item_mlp", "item_mlp", "imlp", "(64,32)", lambda x: list(make_tuple(str(x))), lambda x: self._batch_remove(str(x), " []").replace(",", "-")),
            ("_neg_ratio", "neg_ratio", "negratio", 5, None, None),
            ("_reg", "reg", "reg", 0.001, None, None),
            ("_similarity", "similarity", "sim", "cosine", None, None)
        ]
        self.autoset_params()

        self._max_ratings = np.max(self._data.sp_i_train_ratings)
        self._transactions_per_epoch = self._data.transactions + self._neg_ratio * self._data.transactions

        if self._batch_size < 1:
            self._batch_size = self._data.transactions + self._neg_ratio * self._data.transactions

        self._sampler = pws.Sampler(self._data.i_train_dict, self._data.sp_i_train_ratings, self._neg_ratio)

        self._ratings = self._data.train_dict
        self._sp_i_train = self._data.sp_i_train
        self._i_items_set = list(range(self._num_items))

        self._model = DeepMatrixFactorizationModel(self._num_users, self._num_items, self._user_mlp,
                                                   self._item_mlp, self._reg,
                                                   self._similarity, self._max_ratings,
                                                   self._data.sp_i_train_ratings, self._learning_rate)

    @property
    def name(self):
        return "DMF"\
               + "_e:" + str(self._epochs) \
               + "_bs:" + str(self._batch_size) \
               + f"_{self.get_params_shortcut()}"

    def train(self):
        if self._restore:
            return self.restore_weights()

        best_metric_value = 0

        for it in range(self._epochs):
            loss = 0
            steps = 0
            with tqdm(total=int(self._transactions_per_epoch // self._batch_size), disable=not self._verbose) as t:
                for batch in self._sampler.step(self._transactions_per_epoch, self._batch_size):
                    steps += 1
                    loss += self._model.train_step(batch)
                    t.set_postfix({'loss': f'{loss.numpy() / steps:.5f}'})
                    t.update()

            if not (it + 1) % self._validation_rate:
                recs = self.get_recommendations(self.evaluator.get_needed_recommendations())
                result_dict = self.evaluator.eval(recs)
                self._results.append(result_dict)

                print(f'Epoch {(it + 1)}/{self._epochs} loss {loss/steps:.5f}')

                if self._results[-1][self._validation_k]["val_results"][self._validation_metric] > best_metric_value:
                    print("******************************************")
                    best_metric_value = self._results[-1][self._validation_k]["val_results"][self._validation_metric]
                    if self._save_weights:
                        self._model.save_weights(self._saving_filepath)
                    if self._save_recs:
                        store_recommendation(recs, self._config.path_output_rec_result + f"{self.name}-it:{it + 1}.tsv")

    def get_recommendations(self, k: int = 100):
        predictions_top_k = {}
        for index, offset in enumerate(range(0, self._num_users, self._batch_size)):
            offset_stop = min(offset + self._batch_size, self._num_users)
            predictions = self._model.get_recs(
                (
                    np.repeat(np.array(list(range(offset, offset_stop)))[:, None], repeats=self._num_items, axis=1),
                    np.array([self._i_items_set for _ in range(offset, offset_stop)])
                 )
            )
            v, i = self._model.get_top_k(predictions, self.get_train_mask(offset, offset_stop), k=k)
            items_ratings_pair = [list(zip(map(self._data.private_items.get, u_list[0]), u_list[1]))
                                  for u_list in list(zip(i.numpy(), v.numpy()))]
            predictions_top_k.update(dict(zip(map(self._data.private_users.get,
                                                  range(offset, offset_stop)), items_ratings_pair)))
        return predictions_top_k
