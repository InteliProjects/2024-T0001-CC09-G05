import pandas as pd

# Importa o módulo de logging para registro de eventos
import logging
# Configura o logger para o nome do módulo atual
logger = logging.getLogger(__name__)


class DataPreparation:
    @staticmethod
    def prepare_data(purchases_dt: pd.DataFrame, sells_dt: pd.DataFrame):
        # Registra uma mensagem informativa
        logging.info("Preparing data")

        # Remove linhas com valores ausentes em 'Quantidade' e 'Valor Líquido' nos DataFrames de compras e vendas
        purchases_dt = purchases_dt.dropna(subset=["Quantidade", "Valor Líquido"])
        sells_dt = sells_dt.dropna(subset=["Quantidade", "Valor Líquido"])
        
        # Converte as colunas de data para o tipo datetime
        sells_dt['Dt. Operação'] = pd.to_datetime(sells_dt['Dt. Operação'])
        sells_dt['Vencimento'] = pd.to_datetime(sells_dt['Vencimento'])
        
        # Converte valores de texto para float e remove vírgulas das colunas numéricas
        sells_dt["Quantidade"] = sells_dt["Quantidade"].astype(str).replace(",","", regex=True).astype(float)
        sells_dt["Valor Líquido"] = sells_dt["Valor Líquido"].astype(str).replace(",","", regex=True).astype(float)
        sells_dt["Preço"] = sells_dt["Preço"].astype(str).replace(",","", regex=True).astype(float)
        purchases_dt["Quantidade"] = purchases_dt["Quantidade"].astype(str).replace(",","", regex=True).astype(float)
        purchases_dt["Valor Líquido"] = purchases_dt["Valor Líquido"].astype(str).replace(",","", regex=True).astype(float)
        purchases_dt["Preço"] = purchases_dt["Preço"].astype(str).replace(",","", regex=True).astype(float)
        
        # Converte a coluna 'Dt. Operação' para o tipo datetime
        purchases_dt['Dt. Operação'] = pd.to_datetime(purchases_dt['Dt. Operação'])
        
        # Converte a porcentagem na coluna 'DI' para valores decimais
        sells_dt['DI'] = sells_dt['DI'].str.replace('%', '').astype(float) / 100
        
        # Cria uma coluna 'UniqueID' concatenando várias colunas para identificação única
        sells_dt['UniqueID'] = sells_dt['Cód. Cliente'] + '_' + sells_dt['Dt. Operação'].astype(str) + '_' + sells_dt['Cód. Título'] + '_' + sells_dt['Cód. Corretora']
        purchases_dt['UniqueID'] = purchases_dt['Cód. Cliente'] + '_' + purchases_dt['Dt. Operação'].astype(str) + '_' + purchases_dt['Cód. Título'] + '_' + purchases_dt['Cód. Corretora']
        
        # Remove colunas desnecessárias dos DataFrames de vendas e compras
        sells_dt.drop(['Cód. Cliente', 'Cód. Título', 'Cód. Corretora', 'Tipo'], axis=1, inplace=True)
        purchases_dt.drop(['Cód. Cliente', 'Cód. Título','Vencimento', 'Cód. Corretora', 'Tipo', 'Dt. Liquidação'], axis=1, inplace=True)
        
        # Adiciona uma coluna 'real_id' que contém os índices originais antes de quaisquer operações de filtragem
        purchases_dt["real_id"] = purchases_dt.index
        sells_dt["real_id"] = sells_dt.index
        
        # Filtra as linhas onde 'Dt. Operação' é diferente de 'Vencimento' no DataFrame de vendas
        sells_dt = sells_dt[sells_dt["Dt. Operação"] != sells_dt["Vencimento"]]

        # Retorna os DataFrames de compras e vendas preparados
        return purchases_dt, sells_dt

    @staticmethod
    def group_data(purchases_dt: pd.DataFrame, sells_dt: pd.DataFrame):
        # Registra uma mensagem informativa
        logging.info("Grouping data")

        # Agrupa os DataFrames de compras e vendas pelos valores únicos de 'UniqueID'
        sells_grouped = sells_dt.groupby("UniqueID")
        purchases_grouped = purchases_dt.groupby("UniqueID")
        
        # Retorna os DataFrames agrupados
        return purchases_grouped, sells_grouped
