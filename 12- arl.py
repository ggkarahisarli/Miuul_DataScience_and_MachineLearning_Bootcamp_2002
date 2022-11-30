############################################
# ASSOCIATION RULE LEARNING (BİRLİKTELİK KURALI ÖĞRENİMİ)
############################################

# 1. Veri Ön İşleme
# 2. ARL Veri Yapısını Hazırlama (Invoice-Product Matrix)
# 3. Birliktelik Kurallarının Çıkarılması
# 4. Çalışmanın Scriptini Hazırlama
# 5. Sepet Aşamasındaki Kullanıcılara Ürün Önerisinde Bulunmak


###############################################################
# İş Problemi
###############################################################

# Birliktelik Kuralı temelli bir algoritma ile
# Sepet Aşamasındaki Kullanıcılara Ürün Önerisinde Bulunmak

# Veri Seti Hikayesi
# https://archive.ics.uci.edu/ml/datasets/Online+Retail+II

# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının
# 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içeriyor.


###############################################################
# Değişkenler
###############################################################

# InvoiceNo: Fatura numarası. Her işleme yani faturaya ait eşsiz numara.
# C ile başlıyorsa iptal edilen işlem.

# StockCode: Ürün kodu. Her bir ürün için eşsiz numara.

# Description: Ürün ismi

# Quantity: Ürün adedi. Faturalardaki ürünlerden kaçar tane satıldığını ifade etmektedir.

# InvoiceDate: Fatura tarihi ve zamanı.

# UnitPrice: Ürün fiyatı (Sterlin cinsinden)

# CustomerID: Eşsiz müşteri numarası

# Country: Ülke ismi. Müşterinin yaşadığı ülke.


############################################
# 1. Veri Ön İşleme
############################################

# !pip install mlxtend
import pandas as pd
pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option('display.width', 500)
# çıktının tek bir satırda olmasını sağlar.
pd.set_option('display.expand_frame_repr', False)
from mlxtend.frequent_patterns import apriori, association_rules

# https://archive.ics.uci.edu/ml/datasets/Online+Retail+II

df_ = pd.read_excel("datasets/Recommendation Systems Datasets/online_retail_II.xlsx",
                    sheet_name="Year 2010-2011")

# Exel okuturken problem olursa olası çözüm:
# pip install openpyxl
# df_ = pd.read_excel("datasets/online_retail_II.xlsx",
#                     sheet_name="Year 2010-2011", engine="openpyxl")

df = df_.copy()
df.head()

df.describe().T
df.isnull().sum()
df.shape

# Quantity ve Price daki eksi değerleri istemiyoruz.
# Eksik değer istemiyoruz.
# İade faturaları da çıkaracağız.

def retail_data_prep(dataframe):
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]
    dataframe = dataframe[dataframe["Quantity"] > 0]
    dataframe = dataframe[dataframe["Price"] > 0]
    return dataframe

df = retail_data_prep(df)

# Sayısal değişkenlerdeki otlier değerli kırpacağız.

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

#Tüm hazırlıkların birleştirildiği fonksiyon:
def retail_data_prep(dataframe):
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]
    dataframe = dataframe[dataframe["Quantity"] > 0]
    dataframe = dataframe[dataframe["Price"] > 0]
    replace_with_thresholds(dataframe, "Quantity")
    replace_with_thresholds(dataframe, "Price")
    return dataframe


df = retail_data_prep(df)
#Böylece veriyi hazır hale getiriyoruz.

df.isnull().sum()
df.describe().T


############################################
# 2. ARL Veri Yapısını Hazırlama (Invoice-Product Matrix)
############################################

df.head()

# Description   NINE DRAWER OFFICE TIDY   SET 2 TEA TOWELS I LOVE LONDON    SPACEBOY BABY GIFT SET
# Invoice
# 536370                              0                                 1                       0
# 536852                              1                                 0                       1
# 536974                              0                                 0                       0
# 537065                              1                                 0                       0
# 537463                              0                                 0                       1

# Sadece bir ülkeye indirgedik:
df_fr = df[df['Country'] == "France"]
# Her bir faturadaki her bir üründen kaçar tane olduğunu belirledik:
df_fr.groupby(['Invoice', 'Description']).agg({"Quantity": "sum"}).head(20)
# unstack veya pivot fonksiyonu ile sütunlara değer geçiririz.
# İsimlendirmeleri değişken isimlerine çeviriyoruz:
df_fr.groupby(['Invoice', 'Description']).agg({"Quantity": "sum"}).unstack().iloc[0:5, 0:5]
# NA olan yerleri 0 ile dolduruyoruz fillna fonk ile:
df_fr.groupby(['Invoice', 'Description']).agg({"Quantity": "sum"}).unstack().fillna(0).iloc[0:5, 0:5]
# Ürün sepette yer alıyorsa 1 yazıyoruz:
# Ürünlerin isimleri yerine id ler kullanmak mantıklı!
df_fr.groupby(['Invoice', 'StockCode']). \
    agg({"Quantity": "sum"}). \
    unstack(). \
    fillna(0). \
    applymap(lambda x: 1 if x > 0 else 0).iloc[0:5, 0:5]
# applymap bütün gözlemleri gezer.

#Tüm bu işlemleri yapan fonksiyonumuz:
def create_invoice_product_df(dataframe, id=False):
    if id:
        return dataframe.groupby(['Invoice', "StockCode"])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)
    else:
        return dataframe.groupby(['Invoice', 'Description'])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)

fr_inv_pro_df = create_invoice_product_df(df_fr)

# Invoice-Product Matrix elde edildi:
fr_inv_pro_df = create_invoice_product_df(df_fr, id=True)

# id nin hangi ürün olduğunu check eden fonksiyon:
# values[0]: string olarak değişkene eriştik
# tolist(): listeye çevirik
def check_id(dataframe, stock_code):
    product_name = dataframe[dataframe["StockCode"] == stock_code][["Description"]].values[0].tolist()
    print(product_name)


check_id(df_fr, 10120)

############################################
# 3. Birliktelik Kurallarının Çıkarılması
############################################
#Bool olmalı hatası verdiği için boola çevirdik!
frequent_itemsets = apriori(fr_inv_pro_df.astype('bool'),
                            min_support=0.01,
                            use_colnames=True)
# item setlerin kombinasyonlarının birlikte gözlenme olasılıklarını hesapladık.
# apriori fonk bunu yapıyor.
frequent_itemsets.sort_values("support", ascending=False)

# association_rules fonksiyonu ile kuralları oluşturduk.
# Tüm değerlerin olduğu tablomuz var:
rules = association_rules(frequent_itemsets,
                          metric="support",
                          min_threshold=0.01)

rules[(rules["support"]>0.05) & (rules["confidence"]>0.1) & (rules["lift"]>5)]

check_id(df_fr, 21086)

rules[(rules["support"]>0.05) & (rules["confidence"]>0.1) & (rules["lift"]>5)]. \
sort_values("confidence", ascending=False)

############################################
# 4. Çalışmanın Scriptini Hazırlama
############################################

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

def retail_data_prep(dataframe):
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]
    dataframe = dataframe[dataframe["Quantity"] > 0]
    dataframe = dataframe[dataframe["Price"] > 0]
    replace_with_thresholds(dataframe, "Quantity")
    replace_with_thresholds(dataframe, "Price")
    return dataframe


def create_invoice_product_df(dataframe, id=False):
    if id:
        return dataframe.groupby(['Invoice', "StockCode"])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)
    else:
        return dataframe.groupby(['Invoice', 'Description'])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)


def check_id(dataframe, stock_code):
    product_name = dataframe[dataframe["StockCode"] == stock_code][["Description"]].values[0].tolist()
    print(product_name)


def create_rules(dataframe, id=True, country="France"):
    dataframe = dataframe[dataframe['Country'] == country]
    dataframe = create_invoice_product_df(dataframe, id)
    frequent_itemsets = apriori(dataframe.astype('bool'), min_support=0.01, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="support", min_threshold=0.01)
    return rules

df = df_.copy()

df = retail_data_prep(df)
rules = create_rules(df)

rules[(rules["support"]>0.05) & (rules["confidence"]>0.1) & (rules["lift"]>5)]. \
sort_values("confidence", ascending=False)

############################################
# 5. Sepet Aşamasındaki Kullanıcılara Ürün Önerisinde Bulunmak
############################################

# Örnek:
# Kullanıcı örnek ürün id: 22492

product_id = 22492
check_id(df, product_id)

sorted_rules = rules.sort_values("lift", ascending=False)

recommendation_list = []

for i, product in enumerate(sorted_rules["antecedents"]):
    for j in list(product):
        if j == product_id:
            recommendation_list.append(list(sorted_rules.iloc[i]["consequents"])[0])

recommendation_list[0:3]

check_id(df, 22326)

def arl_recommender(rules_df, product_id, rec_count=1):
    sorted_rules = rules_df.sort_values("lift", ascending=False)
    recommendation_list = []
    for i, product in enumerate(sorted_rules["antecedents"]):
        for j in list(product):
            if j == product_id:
                recommendation_list.append(list(sorted_rules.iloc[i]["consequents"])[0])

    return recommendation_list[0:rec_count]


arl_recommender(rules, 22492, 1)
arl_recommender(rules, 22492, 2)
arl_recommender(rules, 22492, 3)





