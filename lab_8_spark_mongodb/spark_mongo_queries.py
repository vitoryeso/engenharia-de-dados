from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from pymongo import MongoClient

# Conectando ao banco de dados MongoDB
client = MongoClient("mongodb://InovAI-WS-20:27017/")
db = client["discentes_ufrn"]

# Crie um SparkSession
spark = SparkSession.builder.appName("Discentes UFRN") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.2") \
    .getOrCreate()

# Defina o esquema do DataFrame
schema = StructType([
    StructField("matricula", StringType(), True),
    StructField("ano_ingresso", StringType(), True),
    StructField("periodo_ingresso", StringType(), True),
    StructField("id_curso", StringType(), True),
    StructField("id_unidade", StringType(), True),
    StructField("id_unidade_gestora", StringType(), True),
    StructField("nome_discente", StringType(), True),
    StructField("sexo", StringType(), True),
    StructField("forma_ingresso", StringType(), True),
    StructField("tipo_discente", StringType(), True),
    StructField("status", StringType(), True),
    StructField("sigla_nivel_ensino", StringType(), True),
    StructField("nivel_ensino", StringType(), True),
    StructField("nome_curso", StringType(), True),
    StructField("modalidade_educacao", StringType(), True),
    StructField("nome_unidade", StringType(), True),
    StructField("nome_unidade_gestora", StringType(), True)
])

# Leia o arquivo e crie o DataFrame
rdd = spark.sparkContext.textFile("hdfs://localhost:9000/user/ye/discentes-2024.csv")
df = rdd.map(lambda x: x.split(";")).toDF(schema)

# Exibindo o schema do DataFrame
df.printSchema()

# Inserindo os dados no banco de dados MongoDB
df.write.format("mongo").option("uri", "mongodb://localhost:27017/").option("database", "discentes_ufrn").option("collection", "discentes").save()

# Listar todos os alunos que ingressaram por meio do SiSU
df_sisu = df.filter(df["_1"] == "SiSU")
df_sisu.show()
df_sisu.write.format("mongo").option("uri", "mongodb://localhost:27017/").option("database", "discentes_ufrn").option("collection", "discentes_sisu").save()

# Computar quantos alunos são do sexo masculino e do sexo feminino
df_sexo = df.groupBy("_2").count()
df_sexo.show()
df_sexo.write.format("mongo").option("uri", "mongodb://localhost:27017/").option("database", "discentes_ufrn").option("collection", "discentes_sexo").save()

# Computar o top 5 dos cursos que mais receberam alunos
df_cursos = df.groupBy("_3").count().orderBy("_3", ascending=False).limit(5)
df_cursos.show()
df_cursos.write.format("mongo").option("uri", "mongodb://localhost:27017/").option("database", "discentes_ufrn").option("collection", "discentes_cursos").save()

# Realizar consulta múltipla ("relacional")
df_sisu_masculino = df.filter((df["_1"] == "SiSU") & (df["_2"] == "Masculino"))
df_sisu_masculino.show()
df_sisu_masculino.write.format("mongo").option("uri", "mongodb://localhost:27017/").option("database", "discentes_ufrn").option("collection", "discentes_sisu_masculino").save()

# Fechando a sessão Spark
spark.stop()

