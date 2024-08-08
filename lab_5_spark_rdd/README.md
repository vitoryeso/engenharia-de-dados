# Desenvolvimento de Aplicação em PySpark

Este documento descreve os passos necessários para desenvolver uma aplicação utilizando PySpark sobre o conjunto de dados "conjunto2".

## Objetivo

Desenvolver uma aplicação sobre o conjunto de dados "conjunto2", que representa uma folha de pagamento de funcionários de uma empresa qualquer. A aplicação deve ler todos os cargos e apresentar a quantidade de pessoas nos mesmos. Devem ser utilizados os conceitos de RDD em PySpark, retirando as duplicatas antes de fazer a contagem de pessoas.

## Requisitos

- Apache Spark instalado
- PySpark configurado
- Conjunto de dados "conjunto2.csv" disponível em: [conjunto2.csv](https://goo.gl/A3MhFS)

## Passos para Desenvolver a Aplicação

1. **Configuração do Ambiente**

    Certifique-se de que o PySpark está instalado e configurado corretamente em seu ambiente.

2. **Leitura do Conjunto de Dados**

    Utilize o PySpark para ler o conjunto de dados "conjunto2.csv" do HDFS. Aqui está um exemplo de como fazer isso:
    ```python
    from pyspark import SparkConf, SparkContext

    # Crie um contexto Spark
    conf = SparkConf().setAppName("Folha de Pagamento")
    sc = SparkContext(conf=conf)

    # Leia o arquivo de dados
    rdd = sc.textFile("hdfs://localhost:9000/user/ye/conjunto2.csv")
    ```

3. **Processamento dos Dados**

    - **Remover a Segunda Linha**

        Utilize `zipWithIndex` e `filter` para remover a segunda linha:
        ```python
        rdd = rdd.zipWithIndex().filter(lambda x: x[1] != 1).map(lambda x: x[0])
        ```

    - **Remover Duplicatas**

        Utilize o método `distinct` para remover as duplicatas:
        ```python
        rdd = rdd.distinct()
        ```

    - **Extrair e Contar Cargos**

        - Extraia os cargos de cada linha do conjunto de dados.
        - Conte a quantidade de pessoas em cada cargo.
        
        Aqui está um exemplo de como fazer isso:
        ```python
        # Separe as linhas em cargos
        cargos = rdd.map(lambda linha: linha.split(";")[1])

        # Conta a quantidade de pessoas em cada cargo
        contagem = cargos.map(lambda cargo: (cargo, 1)).reduceByKey(lambda a, b: a + b)
        ```

    - **Ordenar os Resultados**

        Ordene os cargos com as contagens em ordem decrescente:
        ```python
        contagem = contagem.sortBy(lambda x: x[1], ascending=False)
        ```

4. **Exibição dos Resultados**

    Colete e exiba os resultados:
    ```python
    resultados = contagem.collect()
    for resultado in resultados:
        print(resultado)
    ```

## Observações

- É importante não utilizar DataFrames, apenas RDDs.
- Certifique-se de ajustar o caminho do arquivo "conjunto2.csv" no HDFS de acordo com o local onde ele está salvo em seu ambiente.

## Exemplo Completo de Código

```python
from pyspark import SparkConf, SparkContext

# Crie um contexto Spark
conf = SparkConf().setAppName("Folha de Pagamento")
sc = SparkContext(conf=conf)

# Leia o arquivo de dados
rdd = sc.textFile("hdfs://localhost:9000/user/ye/conjunto2.csv")

# Remover a segunda linha
rdd = rdd.zipWithIndex().filter(lambda x: x[1] != 1).map(lambda x: x[0])

# Remova as linhas duplicatas
rdd = rdd.distinct()

# Separe as linhas em cargos
cargos = rdd.map(lambda linha: linha.split(";")[1])

# Conta a quantidade de pessoas em cada cargo
contagem = cargos.map(lambda cargo: (cargo, 1)).reduceByKey(lambda a, b: a + b)

# Ordene os cargos com as contagens em ordem decrescente
contagem = contagem.sortBy(lambda x: x[1], ascending=False)

resultados = contagem.collect()
for resultado in resultados:
    print(resultado)

