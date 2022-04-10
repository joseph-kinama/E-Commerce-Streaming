from grpc import unary_stream_rpc_method_handler
from pyspark.sql import SparkSession
from pyspark.sql import functions as func
import json
import pyspark.sql as sql

spark = SparkSession.builder\
    .master('local')\
    .config("spark.mongodb.input.uri", "mongodb://127.0.0.1/test")\
    .config("spark.mongodb.output.uri", "mongodb://127.0.0.1/test")\
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

user_data = spark.read.format("com.mongodb.spark.sql.DefaultSource")\
    .option("database", "test")\
    .option("collection", "user")\
    .load().createOrReplaceTempView('user_data')
order_data = spark.read.format("com.mongodb.spark.sql.DefaultSource")\
    .option("database", "test")\
    .option("collection", 'Orders')\
    .load().createOrReplaceTempView("order_data")


u_data = spark.sql(
    """SELECT
    _id.oid as User_id,
    firstName,
    lastName,
    email,
    cast(phoneNumber as int) as phoneNumber,
    registered.when as registration_date
    FROM user_data"""
)
o_data = spark.sql(
    """Select
    _id.oid as Order_id,
    user.oid as u_id,
    orderNumber,
    products,
    transform(
        products.price,(x,i) -> products.quantity[i]*x
    ) as total_array_price,
    size(products) as total_count,
    stage
    from order_data
    """
)
o_data = o_data.withColumn(
    "total_price",
    func.expr("""round(
        aggregate(
            total_array_price ,
            double(0),
        (acc,x)->acc+x),2)""")
).withColumn(
    "most_exp_price",
    func.expr("array_max(total_array_price)")

).withColumn(
    "highest_prod_price",
    func.expr("array_max(products.quantity)")
).withColumn(
    "most_exp_prod",
    func.expr(
        """products.product[
            array_position(
                total_array_price,
                array_max(total_array_price)
            )
        ].oid"""
    )
).withColumn(
    "highest_quan_prod",
    func.expr("""products.product[
            array_position(
                products.quantity,
                array_max(products.quantity)
            )
         ].oid""")
)


join_stmt = u_data['User_id'] == o_data["u_id"]
joined_data = u_data.join(o_data, join_stmt, "inner")

user_order_data = joined_data.select(
    "User_id", "Order_id", "orderNumber", "total_price",
    "total_count", "highest_quan_prod", "highest_prod_price", "most_exp_prod",
    "stage", "most_exp_price"
)

joined_data.printSchema()
user_order_data.printSchema()
user_order_summary = user_order_data\
    .groupBy("User_id").agg(
        func.count("Order_id").alias("Order_id_count"),
        func.sum("total_price").alias("total_sum"),
        func.avg("total_price").alias("avg_price"),
        func.sum("total_count").alias("total_count_sum"),
        func.max("most_exp_price").alias("exp_price"),
        func.max("highest_prod_price").alias("highest_item")
    )
user_order_summary = user_order_summary.withColumnRenamed(
    "User_id", "user_id_sum"
)
cols = [i for i in user_order_summary.columns]
user_order_summary = user_order_summary.join(
    user_order_data,
    user_order_data["User_id"] == user_order_summary["user_id_sum"]
).filter(
    user_order_data["most_exp_price"] == user_order_summary["exp_price"]
).select(
    *cols, func.col("most_exp_prod")
)
cols = [i for i in user_order_summary.columns]

user_order_summary = user_order_summary.join(
    user_order_data,
    user_order_data["User_id"] == user_order_summary["user_id_sum"]
).filter(
    user_order_data["highest_prod_price"] == user_order_summary["highest_item"]
).select(
    *cols, func.col("highest_quan_prod")
)


# avg
# categories
# cart to order transition
# user_order_data.show(1)

user_order_summary.show(1)
user_order_summary.printSchema()