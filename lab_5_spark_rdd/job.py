from pyspark import SparkConf, SparkContext

# Crie um contexto Spark
conf = SparkConf().setAppName("Folha de Pagamento")
sc = SparkContext(conf=conf)

# Leia o arquivo de dados
rdd = sc.textFile("hdfs://localhost:9000/user/ye/conjunto2.csv")

# remover a segunda linha
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
