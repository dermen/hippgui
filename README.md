# CTFS data processing tool

##Table of Contents
1. Introduction
2. Loading data into MYSQL
3. Standardize the data

##1. Introduction
Trees persist for many years, and consequently tree databases can get messy. The **CTFS data processing tool** aims to aid in the processing of tree census data (diameter at breast height measurements, also known as *dbh* measurements), recorded for the same trees over many years.

Typically a database will consists of several data tables. Each table will have separate columns, namely

* **dbh**: The dimater of the tre at breast height

* **pom**: The point of measurement (typically 130 centi-meters)

* **status**: The state of the tree (e.g. *alive*, *dead*, *missing*, *broken*, *new main stem*, *etc.*). Initial censuse data tables should have the *alive* status for every tree.

* **date**: when the measurement was recorded, in a standard date format (e.g. *11/09/1989* for *November, 9th 1989*). The date format does not need to be specific, but should be consistent and typical. Further, each row of the data table should contain a date. 

* **species**: The species of the tree. Typically this is a mneumonic used in the field, which is the first 3 letters of the Genus, followed by the first three letters of the species epithet (e.g. *ACAKOA* for *Acacia koa*). This should be consistent throughout.

* **x**: the x coordinate of the tree (e.g. in universal transverse mercador coordinates)

* **y**: the y coordinate of the tree (in the same units as *x*)


##2. Loading data into MYSQL

The first step in the data processing is to put the data into [MYSQL](https://www.mysql.com/). MYSQL has several advatntages over the average user database:

* It is a light-weight query language that is designed to process large databases efficiently. 
* It is cross platform database (works on MAC, Windows and Linux).
* CTFS data can easily be shared with the global community in this format. 

Data can be loaded into MYSQL in several ways. Here are but a few: 

* **If my your database is in Acess:**
 * Use Bullzip's [Access to mysql](http://www.bullzip.com/download.php) package. 

* **If my database is many Excel tables:**
 * If you are using windows, then download [Mysql for excel](http://dev.mysql.com/downloads/windows/excel/) tool. Then, follow the steps [here](http://dev.mysql.com/doc/mysql-for-excel/en/mysql-for-excel-export.html).

* **If my data is in many text files and/or you cannot use the above:**
 * Save the data as **txt/tab-delimited** (TSV) format and follow [these steps](http://stackoverflow.com/a/13579922/2077270)

##3. Standardize the data

As the years progress and recensusing begins, chances are the data will begin to get messy.  For instance, the tree status column (which designates whether the tree is *alive*, *dead*, *missing*, *etc.*) often times will conatain 
