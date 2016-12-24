import unicodedata

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import TransformerMixin
from sklearn.cluster import KMeans


class MealPriceOutlierClassifier(TransformerMixin):


    HOTEL_REGEX = r'hote(?:(?:ls?)|is)'
    CLUSTER_KEYS = ['mean', 'std']

    def fit(self, X):
        _X = X[self.__applicable_rows(X)]
        companies = _X.groupby('cnpj_cpf').apply(self.__company_stats) \
            .reset_index()
        companies = companies[self.__applicable_company_rows(companies)]

        self.cluster_model = KMeans(n_clusters=3)
        self.cluster_model.fit(companies[self.CLUSTER_KEYS])
        companies['cluster'] = self.cluster_model.predict(companies[self.CLUSTER_KEYS])
        self.clusters = companies.groupby('cluster') \
            .apply(self.__cluster_stats) \
            .reset_index()
        self.clusters['threshold'] = \
            self.clusters['mean'] + 4 * self.clusters['std']
        return self

    def transform(self, X=None):
        pass

    def predict(self, X):
        return self.__predict(X)['y']

    def predict_proba(self, X):
        return np.r_[self.__predict(X)['probability']]

    def __predict(self, X):
        _X = X.copy()
        companies = _X[self.__applicable_rows(_X)] \
            .groupby('cnpj_cpf').apply(self.__company_stats) \
            .reset_index()
        companies['cluster'] = \
            self.cluster_model.predict(companies[self.CLUSTER_KEYS])
        companies = pd.merge(companies,
                             self.clusters,
                             how='left',
                             on='cluster',
                             suffixes=['', '_cluster'])
        _X = pd.merge(_X, companies, how='left', on='cnpj_cpf')
        rows = self.__applicable_rows(_X)
        _X['probability'] = float('nan')
        _X.loc[rows, 'probability'] = \
            self.__probability(_X[rows], 4, col_suffix='_cluster')
        known_companies = companies[self.__applicable_company_rows(companies)]
        known_thresholds = known_companies \
            .groupby('cnpj_cpf') \
            .apply(lambda x: x['mean'] + 3 * x['std']) \
            .reset_index() \
            .rename(columns={0: 'cnpj_threshold'})
        _X = pd.merge(_X, known_thresholds, how='left')
        if 'cnpj_threshold' in _X.columns:
            rows = rows & _X['cnpj_threshold'].notnull()
            _X.loc[rows, 'threshold'] = _X['cnpj_threshold']
            _X.loc[rows, 'probability'] = self.__probability(_X[rows])
        _X['y'] = 1
        is_outlier = self.__applicable_rows(_X) & \
            _X['threshold'].notnull() & \
            (_X['total_net_value'] > _X['threshold'])
        _X.loc[is_outlier, 'y'] = -1
        return _X

    def __probability(self, X, stds_threshold=3, col_suffix=''):
        mean_col, std_col = 'mean' + col_suffix, 'std' + col_suffix
        return 1 - stats.norm.pdf(stds_threshold, X[mean_col], X[std_col]) / 2

    def __applicable_rows(self, X):
        return (X['subquota_description'] == 'Congressperson meal') & \
            (X['cnpj_cpf'].str.len() == 14) & \
            (~X['supplier'].apply(self.__normalize_string).str.contains(self.HOTEL_REGEX))

    def __applicable_company_rows(self, companies):
        return (companies['congresspeople'] > 3) & (companies['records'] > 20)

    def __company_stats(self, X):
        stats = {'mean': np.mean(X['total_net_value']),
                 'std': np.std(X['total_net_value']),
                 'congresspeople': len(np.unique(X['applicant_id'])),
                 'records': len(X)}
        return pd.Series(stats)

    def __cluster_stats(self, X):
        stats = {'mean': np.mean(X['mean']),
                 'std': np.mean(X['std'])}
        return pd.Series(stats)

    def __normalize_string(self, string):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
