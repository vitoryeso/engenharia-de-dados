Instalação e Configuração do Hadoop no Linux

Este documento descreve os passos necessários para instalar e configurar o Hadoop no Linux.

Requisitos

* Sistema operacional Linux
* Java 11 ou superior instalado
* Conexão à internet para baixar os pacotes necessários

Passos de Instalação

1. Baixe o pacote do Hadoop da página oficial do Apache Hadoop: <https://hadoop.apache.org/releases.html>
2. Descompacte o pacote em um diretório de sua escolha (por exemplo, `/usr/local/hadoop`)
3. Configure as variáveis de ambiente do Hadoop adicionando as seguintes linhas ao arquivo `/etc/bash.bashrc`:
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
4. Reinicie o terminal ou execute o comando `source ~./.bashrc` para aplicar as alterações

Comandos para Rodar

Para rodar o HDFS e o YARN JAR, execute os seguintes comandos:

* Baixar datasets: `chmod +x download_datasets` `./download_datasets`
* Iniciar o HDFS: `start-dfs.sh`
* Iniciar o YARN: `start-yarn.sh`
* Criar pastas no hdfs: `hdfs dfs -mkdir /user/X`
* Colocar arquivos no hdfs: `hdfs dfs -put datasets/salarios.csv /user/X/` `hdfs dfs -put datasets/dovecot.log /user/X/`
* Rodar o YARN JAR: `hadoop jar /usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.jar -mapper mapper_email.py -reducer reducer_email.py -input /user/X/dovecot.log -output /user/X/output`

Lembre-se de substituir `/user/ye/dovecot.log` e `/user/ye/output` pelos caminhos corretos para o arquivo de entrada e saída, respectivamente.

