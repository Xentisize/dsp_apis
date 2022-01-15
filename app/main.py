import os

import numpy as np
import pandas as pd
import seaborn
from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from matplotlib import pyplot as plt
from pydantic import BaseModel, HttpUrl

app = FastAPI()
app.mount("/figures", StaticFiles(directory="./figures"), name="figures")

origins = [
    "*",
    "http://localhost:8080",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers="*",
)


class FileMetaData(BaseModel):
    name: str
    verbose_name: str
    path: str
    ext: str
    index: str | list
    sheet_name: int
    header: int | list
    index_col: int | list
    columns: list[str] | list[tuple] = []
    year: int | None
    category: str | None
    description: str
    region: str
    url: HttpUrl | None
    skip_header_rows: int = 0
    skip_footer_rows: int = 0
    descriptive_data: dict | None
    descriptive_plot: str | None


# @app.get("/data/describe")
def describe_data(file: FileMetaData):
    if file.ext == "csv":
        df = pd.read_csv(
            file.path,
            skiprows=file.skip_header_rows,
            skipfooter=file.skip_footer_rows,
            index_col=file.index,
            header=file.header,
        )
    elif file.ext == "xls" or file.ext == "xlsx":
        df = pd.read_excel(
            file.path,
            skiprows=file.skip_header_rows,
            skipfooter=file.skip_footer_rows,
            index_col=file.index,
            sheet_name=file.sheet_name,
            header=file.header,
        )
    return (df.columns.to_list(), df.describe().to_dict())


def brief_plot(file: FileMetaData):
    if file.ext == "csv":
        df = pd.read_csv(
            file.path,
            skiprows=file.skip_header_rows,
            skipfooter=file.skip_footer_rows,
            index_col=file.index,
            header=file.header,
        )
    elif file.ext == "xls" or file.ext == "xlsx":
        df = pd.read_excel(
            file.path,
            skiprows=file.skip_header_rows,
            skipfooter=file.skip_footer_rows,
            index_col=file.index,
            sheet_name=file.sheet_name,
            header=file.header,
        )
    fig = df.hist(figsize=(20, 15))
    plt.savefig(f"./figures/{file.name}.png")
    return f"{file.name}.png"


data_bank = [
    FileMetaData(
        name="property_market_statistics(private_domestic_vacancy).csv",
        verbose_name="Private Domestic Vacancy",
        path="datasets/hong_kong/2021/property_market_statistics(private_domestic_vacancy).csv",
        ext="csv",
        index="Year",
        sheet_name=0,
        header=0,
        index_col=0,
        year=2021,
        category="Property Market",
        description="Private Domestic Vancy updated annually",
        region="Hong Kong SAR",
        url="http://www.rvd.gov.hk/datagovhk/Private_Domestic-Vacancy.csv",
        skip_header_rows=1,
        skip_footer_rows=0,
    ),
    FileMetaData(
        name="valuation_list_assessments_by_district.xls",
        verbose_name="Valuation List - Assessments by District (English)",
        path="datasets/hong_kong/2021/valuation_list_assessments_by_district.xls",
        ext="xls",
        index="District",
        sheet_name=0,
        header=0,
        index_col=0,
        year=2021,
        category="Property Market",
        description="Valuation List - Assessment by District, updated in March and April annually",
        region="Hong Kong SAR",
        url="http://www.rvd.gov.hk/doc/en/statistics/summary_statistics_table_6.xls",
        skip_header_rows=4,
        skip_footer_rows=4,
    ),
    FileMetaData(
        name="gdp_by_major_expenditure_component_and_per_capita_gdp.xlsx",
        verbose_name="GDP by major expenditure component and per capita GDP",
        path="datasets/hong_kong/2021/gdp_by_major_expenditure_component_and_per_capita_gdp.xlsx",
        ext="xlsx",
        index=[0, 1],
        sheet_name=1,
        header=[0, 1],
        index_col=[0, 1],
        year=2021,
        category="Finance",
        description="GDP by major expenditure component and per capita GDP updated quarterly",
        region="Hong Kong SAR",
        url="https://www.censtatd.gov.hk/en/EIndexbySubject.html?pcode=D5240200&scode=250&file=D5240200E2021QQ03E.xlsx",
        skip_header_rows=2,
        skip_footer_rows=17,
    ),
]

for d in data_bank:
    d.descriptive_data = describe_data(d)[1]
    d.descriptive_plot = brief_plot(d)
    d.columns = describe_data(d)[0]

data_bank[2].descriptive_data = {
    "Gross Domestic Product [1]": {
        "HK$ million": {
            "count": 255.0,
            "mean": 435643.9882352941,
            "std": 540654.6155991578,
            "min": 7455.0,
            "25%": 68373.5,
            "50%": 316887.0,
            "75%": 536232.5,
            "max": 2844560.0,
        }
    }
}

# print(type(data_bank[2].descriptive_data.keys()))


@app.get("/data/list_files")
async def list_file(directory: str = Query("./datasets/hong_kong/2021")):
    file_names = os.listdir(directory)
    return file_names


@app.get("/data/show", response_model=FileMetaData)
async def show_data(file: str):
    index = None
    for i, d in enumerate(data_bank):
        if file == d.name:
            index = i
            print("Matched index: ", i)
            break
    # print(data_bank[i])
    return data_bank[i]


@app.get("/data/get_data")
async def get_data(file: str, label: str):
    file_meta = None
    for data in data_bank:
        if file == data.name:
            file_meta = data
            break
    if file_meta:
        if file_meta.ext == "csv":
            df = pd.read_csv(
                file_meta.path,
                skiprows=file_meta.skip_header_rows,
                skipfooter=file_meta.skip_footer_rows,
                index_col=file_meta.index,
                header=file_meta.header,
            )
        elif file_meta.ext == "xls" or file_meta.ext == "xlsx":
            df = pd.read_excel(
                file_meta.path,
                skiprows=file_meta.skip_header_rows,
                skipfooter=file_meta.skip_footer_rows,
                index_col=file_meta.index,
                sheet_name=file_meta.sheet_name,
                header=file_meta.header,
            )
        print(label)

        df_target = df[label]
        return df_target.to_list()
    return {"status": "error"}
