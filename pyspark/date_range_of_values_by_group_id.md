# Challenge
Given this data:
```python
init_dict_list = [
    {"group_id": "g1", "value": 0, "date": "2024-02-29"},
    {"group_id": "g1", "value": 0, "date": "2024-02-28"},
    {"group_id": "g1", "value": 0, "date": "2024-02-27"},
    {"group_id": "g1", "value": 1, "date": "2024-02-26"},
    {"group_id": "g1", "value": 2, "date": "2024-02-25"},
    {"group_id": "g1", "value": 0, "date": "2024-02-24"},
    {"group_id": "g1", "value": 0, "date": "2024-02-23"},
    {"group_id": "g2", "value": 5, "date": "2024-02-29"},
    {"group_id": "g2", "value": 6, "date": "2024-02-28"},
    {"group_id": "g2", "value": 5, "date": "2024-02-27"},
    {"group_id": "g2", "value": 5, "date": "2024-02-26"},
    {"group_id": "g2", "value": 6, "date": "2024-02-25"},
    {"group_id": "g2", "value": 4, "date": "2024-02-24"},
]
```
Consolidate the group_id with value column and create a from_dt and to_dt column that will show the following results:

<img width="433" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/225f1d82-1bbb-464f-b4af-4dd59eb5d06a">

This table shows the the `value`s in the order of the `date` column, descending, with the `from_dt` and `to_dt` being the date associated with the earliest to latest date without break that the `value` column has been repeated for. If there are no repetition across 2 or more consecutive dates, then the `from_dt` and `to_dt` date will be identical.

# Solution

## Import libraries
```python
from pyspark import SparkContext
from pyspark.sql import SparkSession, DataFrame, functions as f
from pyspark.sql.window import Window
```

## Create Spark Session
```python
spark = SparkSession.builder \
  .appName("Data Processing Task") \
  .enableHiveSupport() \
  .config('spark.sql.debug.maxToStringFields', 2000) \
  .config("spark.driver.memory", "9g") \
  .getOrCreate()

sc = spark.sparkContext
```

## Create Initial Spark DataFrame
```python
init_dict_list = [
    {"group_id": "g1", "value": 0, "date": "2024-02-29"},
    {"group_id": "g1", "value": 0, "date": "2024-02-28"},
    {"group_id": "g1", "value": 0, "date": "2024-02-27"},
    {"group_id": "g1", "value": 1, "date": "2024-02-26"},
    {"group_id": "g1", "value": 2, "date": "2024-02-25"},
    {"group_id": "g1", "value": 0, "date": "2024-02-24"},
    {"group_id": "g1", "value": 0, "date": "2024-02-23"},
    {"group_id": "g2", "value": 5, "date": "2024-02-29"},
    {"group_id": "g2", "value": 6, "date": "2024-02-28"},
    {"group_id": "g2", "value": 5, "date": "2024-02-27"},
    {"group_id": "g2", "value": 5, "date": "2024-02-26"},
    {"group_id": "g2", "value": 6, "date": "2024-02-25"},
    {"group_id": "g2", "value": 4, "date": "2024-02-24"},
]
df_init_test = spark.createDataFrame(init_dict_list)
display(df_init_test)
```
<img width="331" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/9614d7ee-66d7-480b-9ef6-e70b1d034908">

## Use Window funtions to find the repeated values, mark the start (from_dt), middle, and end (to_dt) of repeated values
```python
group_id_col = "group_id"
date_col = "date"
value_col = "value"
windowSpec  = Window.partitionBy(group_id_col).orderBy(f.desc(date_col))

df_lag = df_init_test\
    .withColumn("lag_value_up",f.lag(value_col, -1).over(windowSpec))\
    .withColumn("lag_value_dwn",f.lag(value_col, 1).over(windowSpec))\
    .withColumn("rep_flag", f.when(f.expr(f"({value_col} = lag_value_up) or ({value_col} = lag_value_dwn)"), f.lit("true")).otherwise(f.lit("false")))\
    .withColumn("to_n_from_dt",
                f.when(f.expr(f"({value_col} = lag_value_up) and ({value_col} = lag_value_dwn)"), f.lit("middle")).otherwise(
                f.when(f.expr(f"(({value_col} != lag_value_up) or lag_value_up is null) and (rep_flag = 'true')"), f.lit("from_dt")).otherwise(
                f.when(f.expr(f"(({value_col} != lag_value_dwn) or lag_value_dwn is null) and (rep_flag = 'true')"), f.lit("to_dt")).otherwise(f.lit(""))))
    )\
    .withColumn("from_dt",
        f.when(f.expr("to_n_from_dt = 'from_dt'"), f.col("date")).otherwise(
        f.when(f.expr("to_n_from_dt = ''"), f.col("date"))))\
    .withColumn("to_dt",
        f.when(f.expr("to_n_from_dt = 'to_dt'"), f.col("date")).otherwise(
        f.when(f.expr("to_n_from_dt = ''"), f.col("date"))))


display(df_lag)
```
<img width="965" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/dc2281c5-2f15-4729-912a-8a1141d5919b">

## Extract the non-repeated values
```python
# singles
# df_singles = df_lag.filter(f.expr("from_dt is not null and to_dt is not null")) # OR
df_singles = df_lag.filter(f.expr("rep_flag = 'false'"))
display(df_singles)
```
<img width="965" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/d1d85c37-42fd-44e5-90f9-fe902fe3f56d">

## Extract the repeated values by shifting the to_dt column down a row to be on the same level as the from_dt row
```python
# miltiples
df_multiples = df_lag.filter(f.expr("(from_dt is null and to_dt is not null) or (from_dt is not null and to_dt is null)"))
windowSpec  = Window.partitionBy(group_id_col).orderBy(f.desc(date_col))
df_lag_multiples = df_multiples.withColumn("lag_to_dt",f.lag("to_dt", 1).over(windowSpec))
display(df_lag_multiples)
```
<img width="1064" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/ad7be68d-a7c1-4ee8-87d9-4e55340da1c9">

## Union the repeated and non-repeated DataFrames together
```python
df_multiples = df_lag_multiples.selectExpr("group_id", "value", "from_dt", "lag_to_dt as to_dt").filter(f.expr("from_dt is not null"))
union_df = df_multiples.unionByName(df_singles.select("group_id", "value", "from_dt", "to_dt"), allowMissingColumns=True)
display(union_df.orderBy("group_id", "from_dt"))
```
<img width="428" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/e15a8e52-f6d4-4b2d-88a5-fec60dfe4ee8">

## OPTIONAL: Update to_dt with the max date associated with the group id to be the current date
```python
max_date = df_init_test.groupby(group_id_col).agg(f.expr(f"max({date_col})").alias("max_date"))
union_max = union_df.join(max_date, how="inner", on=[group_id_col]).distinct()
union_df_max = union_max.withColumn("to_dt", f.when(f.expr("to_dt = max_date"), f.expr("current_date")).otherwise(f.col("to_dt")))
display(union_df_max)
```
<img width="526" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/cc667aea-29bb-4103-892a-c80f3f9ddad4">

```python
display(union_df_max.select(group_id_col, value_col, "from_dt", "to_dt").orderBy("group_id", "from_dt"))
```
<img width="429" alt="image" src="https://github.com/saeedfalowo/DataManipulation/assets/52696765/23cc135c-f5f4-4979-ab84-a76c034f51c1">
