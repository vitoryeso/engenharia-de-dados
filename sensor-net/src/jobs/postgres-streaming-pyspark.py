from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import SparkSession

# Criar uma instância da classe SparkSession com a configuração para HDFS
spark = SparkSession.builder \
    .appName("Postgres Streaming") \
    .config("spark.sql.session.timeZone", "America/Sao_Paulo") \
    .getOrCreate()

# Criar o dataframe do tipo stream, apontando para o servidor Kafka e o tópico a ser consumido
df = (spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", "192.168.0.2:9092")
      .option("subscribe", "postgres-1.public.sensor_data")
      .option("startingOffsets", "earliest")
      .load()
)

# Definir o schema dos dados inseridos no tópico
schema = StructType([
    StructField("payload", StructType([
        StructField("after", StructType([
            StructField("sensor_type", StringType(), True),
            StructField("measurement", FloatType(), True),
            StructField("timestamp", LongType(), True)  # Tratar como LongType para microssegundos
        ]))
    ]))
])

# Converter o valor dos dados do Kafka de formato binário para JSON
dx = df.select(from_json(df.value.cast("string"), schema).alias("data")).select("data.payload.after.*")

# Converter o timestamp em microssegundos para um formato de data e hora legível
dx = dx.withColumn("timestamp", (col("timestamp") / 1000000).cast("long"))
dx = dx.withColumn("timestamp", from_unixtime("timestamp", "yyyy-MM-dd HH:mm:ss"))


from pyspark.sql.functions import *

# Converter a coluna "timestamp" para o tipo de dados "TIMESTAMP"
dx = dx.withColumn("timestamp", unix_timestamp("timestamp", "yyyy-MM-dd HH:mm:ss").cast("timestamp"))

# Adicione uma marca d'água ao seu DataFrame/DataSet de streaming
dx = dx.withWatermark("timestamp", "10 minutes")

# Calcular a média das medições e o número de medições -1 ou nulas
metrics = (dx
           .groupBy()  # Agregar todos os dados
           .agg(
               avg("measurement").alias("average_measurement"),
               sum(when(col("measurement").isNull() | (col("measurement") == -1), 1).otherwise(0)).alias("count_invalid_measurements")
           ))

# Escrever as métricas em HDFS em formato JSON
query = (metrics.writeStream
         .outputMode("append")
         .format("json")
         .option("path", "hdfs://192.168.0.3:9000/user/ye/sensor.json")
         .start()
)



# Aguardar a terminação do stream
query.awaitTermination()
