import yaml
from pyspark.sql import SparkSession
from pymongo import MongoClient

# Carregue as configurações do arquivo config.yaml
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    # Se o arquivo não existir, use os valores default
    config = {
        'url': 'mongodb://localhost:27017/',
        'database': 'discentes_2024',
        'collection': 'discentes',
        'delimiter': ';',
        'header': True,
        'inferSchema': True,
        'arquivo_entrada': 'hdfs://localhost:9000/user/ye/discentes-2024.csv'
    }

# Crie um SparkSession
spark = SparkSession.builder.appName("Meu App").getOrCreate()

# Leia o arquivo de entrada
df = spark.read.option("header", config['header']).option("inferSchema", config['inferSchema']).option("delimiter", config['delimiter']).csv(config['arquivo_entrada'])

# Conecte ao MongoDB
client = MongoClient(config['url'])
db = client[config['database']]

# Inserção dos dados no MongoDB
try:
    df.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", config['collection']).save()
except Exception as e:
    print("Ocorreu um erro ao inserir os dados no banco de dados discentes_2024.")
    print(e)

# Consultas aos dados
# A primeira consulta é para listar todos os alunos que ingressaram por meio do SiSU
df_sisu = df.filter(df["forma_ingresso"] == "SiSU")

# Computar quantos alunos são do sexo masculino e do sexo feminino
df_sexo = df.groupBy("sexo").count()
df_sexo.show()
try:
    df_sexo.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", "sexo").save()
except Exception as e:
    print("Ocorreu um erro ao escrever os dados no banco de dados discentes_2024.")
    print(e)

# A terceira consulta é para computar o top 5 dos cursos que mais receberam alunos
df_cursos = df.groupBy("nome_curso").count().orderBy("count", ascending=False).limit(5)

# A quarta consulta é para realizar consulta múltipla ("relacional")
# A consulta é para quantos alunos são do sexo masculino que ingressaram via SiSU em algum curso em específico
df_sisu_masculino = df.filter((df["forma_ingresso"] == "SiSU") & (df["sexo"] == "M"))

# Imprima os resultados
df_sisu.show()
df_sexo.show()
df_cursos.show()
df_sisu_masculino.show()

# Escreva os resultados no MongoDB
try:
    df_sisu.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", "sisu").save()
except Exception as e:
    print("Ocorreu um erro ao escrever os dados no banco de dados discentes_2024.")
    print(e)

try:
    df_sexo.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", "sexo").save()
except Exception as e:
    print("Ocorreu um erro ao escrever os dados no banco de dados discentes_2024.")
    print(e)

try:
    df_cursos.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", "cursos").save()
except Exception as e:
    print("Ocorreu um erro ao escrever os dados no banco de dados discentes_2024.")
    print(e)

try:
    df_sisu_masculino.write.format("mongo").option("uri", config['url']).option("database", config['database']).option("collection", "sisu_masculino").save()
except Exception as e:
    print("Ocorreu um erro ao escrever os dados no banco de dados discentes_2024.")
    print(e)

