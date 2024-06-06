import unittest
import pandas as pd
from processing.data_process import DataPreparation

class TestDataPreparation(unittest.TestCase):
    def test_prepare_data(self):
        v = {'Unnamed: 0': [0, 1], 'Chave': ['B2', 'B3'], 'Dt. Operação': [pd.Timestamp('2022-04-01 00:00:00'), pd.Timestamp('2022-06-23 00:00:00')], 'Tipo Operação': ['V', 'V'], 'Quantidade': [8942.0, 9512.0], 'Preço': [18.2, 14.84], 'Valor Líquido': [162754.49, 141162.79], 'Vencimento': [pd.Timestamp('2023-08-18 00:00:00'), pd.Timestamp('2023-10-23 00:00:00')], 'DI': [0.12300000000000001, 0.1321], 'UniqueID': ['Cliente 10_2022-04-01_ABCB4_STDE', 'Cliente 10_2022-06-23_ABCB4_AGOR']}
        c = {'Unnamed: 0': [0, 1], 'Dt. Operação': [pd.Timestamp('2022-04-01 00:00:00'), pd.Timestamp('2022-04-01 00:00:00')], 'Tipo Operação': ['C', 'C'], 'Quantidade': [1236.0, 1360.0], 'Preço': [15.56, 15.88], 'Valor Líquido': [-19232.17, -21593.84], 'UniqueID': ['Cliente 10_2022-04-01_ABCB4_STDE', 'Cliente 10_2022-04-01_ABCB4_STDE'], 'real_id': [0, 1]}

        vendas = pd.read_csv('./v.csv')
        compras = pd.read_csv('./c.csv')
        compras,vendas = DataPreparation.prepare_data(compras,vendas)

        for column in c:
            self.assertListEqual(compras[column].tolist(), c[column], f"Column '{column}' does not match")

        for column in v:
            self.assertListEqual(vendas[column].tolist(), v[column], f"Column '{column}' does not match")

    def test_group_data(self):
        vendas = pd.read_csv('./v.csv')
        compras = pd.read_csv('./c.csv')
        compras,vendas = DataPreparation.prepare_data(compras,vendas)

        purchases_grouped, sells_grouped = DataPreparation.group_data(compras,vendas)

        self.assertEqual(len(purchases_grouped), 1) 
        self.assertEqual(len(sells_grouped), 2) 