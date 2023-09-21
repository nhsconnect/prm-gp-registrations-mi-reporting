import pandas as pd

final_df = pd.DataFrame()
date_dict = {"06": 30, "07": 31, "08": 31}

for month, num_days in date_dict.items():
    for i in range(1, num_days+1):
        day = "0" + str(i) if i < 10 else str(i)
        path = f"~/2023/{month}/{day}/2023-{month}-{day}-transfers.parquet"
        df_raw = pd.read_parquet(path, engine="pyarrow")

        df_icb = df_raw[["conversation_id",
                         "sending_practice_ods_code",
                         "requesting_practice_sicbl_ods_code",
                         "requesting_practice_sicbl_name",
                         "sending_practice_sicbl_ods_code",
                         "sending_practice_sicbl_name"
                         ]]
        df_icb = df_icb[df_icb["sending_practice_ods_code"] == "M85143"]
        del df_icb["sending_practice_ods_code"]

        final_df = pd.concat([final_df, df_icb])

print(final_df.info())

final_df = final_df.groupby(["requesting_practice_sicbl_ods_code",
                             "requesting_practice_sicbl_name",
                             "sending_practice_sicbl_ods_code",
                             "sending_practice_sicbl_name"
                             ]
                            ).count()

final_df = final_df.sort_values(by=["conversation_id"], ascending=False).reset_index()
final_df = final_df.rename(columns={"conversation_id": "num_leaving_patients"})
print(final_df.to_markdown())
