import pandas as pd
from scipy.stats import pearsonr
ethnicity_df = pd.read_excel("Ethnic group.xlsx", sheet_name="2021")
features_df = pd.read_csv("lsoa_features_final.csv")
pd.set_option('display.max_columns', None)

#print(ethnicity_df.head(1))
#print(len(ethnicity_df.columns))
ethnicity_df.columns = [
    "LSOA_code", "LocalAuthority_name","LocalAuthority_code","TotalPop", "WhiteBritish", "WhiteIrish","WhiteTraveler", "WhiteRoma", "WhiteOther", "MixedWhiteAsian",
    "MixedWhiteBlackAfrican", "MixedWhiteBlackCaribbean", "MixedOther","AsianBangladeshi", "AsianChinese",
    "AsianIndian", "AsianPakistani", "OtherAsian",
    "BlackAfrican", "BlackCaribbean", "OtherBlack",
    "Arab", "OtherEthnic"
]
#print(len(ethnicity_df.columns))
ethnicity_df["NonWhiteInclRoma"] = (
    ethnicity_df[["WhiteRoma","MixedWhiteBlackCaribbean", "MixedWhiteBlackAfrican", "MixedWhiteAsian", "MixedOther",
                  "AsianIndian", "AsianPakistani", "AsianBangladeshi", "AsianChinese", "OtherAsian",
                  "BlackAfrican", "BlackCaribbean", "OtherBlack",
                  "Arab", "OtherEthnic"]].sum(axis=1)
)

ethnicity_df["PctNonWhiteInclRoma"] = ethnicity_df["NonWhiteInclRoma"] / ethnicity_df["TotalPop"] * 100
#print(ethnicity_df.head(5))

features_df['month'] = pd.to_datetime(features_df['month'])
features_df['month'] = pd.to_datetime(features_df['month'], format='%Y-%m')

# Filter features_df for months from January 2021 onwards
features_post2021 = features_df[features_df['month'] >= '2021-01-01'].copy()
#print(features_post2021.head(1))
filtred_features = features_post2021[['LSOA code','month', 'y_true']]
#print(filtred_features.head(1))
filtred_features_grouped = filtred_features.groupby('LSOA code', as_index=False)['y_true'].sum()
#print(filtred_features_grouped.head(1))
filtred_features_grouped = filtred_features_grouped.rename(columns={"LSOA code": "LSOA_code"})
merged_df = pd.merge(filtred_features_grouped, ethnicity_df[['LSOA_code', 'PctNonWhiteInclRoma']], on='LSOA_code', how='inner')
print(merged_df.head(5))

ethnicity_df["PctBlack"] = (
    ethnicity_df[["BlackAfrican", "BlackCaribbean", "OtherBlack"]].sum(axis=1) / ethnicity_df["TotalPop"] * 100
)

merged_black = pd.merge(filtred_features_grouped, ethnicity_df[["LSOA_code", "PctBlack"]], on="LSOA_code", how="inner")




ethnicity_df["PctWhite"] = (
    ethnicity_df[["WhiteBritish", "WhiteIrish", "WhiteTraveler", "WhiteOther"]].sum(axis=1)
    / ethnicity_df["TotalPop"] * 100
)

ethnicity_df["PctAsianSubcontinent"] = (
    ethnicity_df[["AsianIndian", "AsianPakistani", "AsianBangladeshi"]].sum(axis=1)
    / ethnicity_df["TotalPop"] * 100
)

ethnicity_df["PctAsianOther"] = (
    ethnicity_df[["AsianChinese", "OtherAsian"]].sum(axis=1)
    / ethnicity_df["TotalPop"] * 100
)

ethnicity_df["PctArab"] = (
    ethnicity_df["Arab"] / ethnicity_df["TotalPop"] * 100
)

ethnicity_percentages_df = ethnicity_df[[
    "LSOA_code",
    "PctNonWhiteInclRoma",
    "PctBlack",
    "PctWhite",
    "PctAsianSubcontinent",
    "PctAsianOther",
    "PctArab"
]]

ethnicity_percentages_df.to_excel("nonwhite_ethnicity_percentage.xlsx", index=False)

r_black, p_black = pearsonr(merged_black['y_true'], merged_black['PctBlack'])

correlation = merged_df['y_true'].corr(merged_df['PctNonWhiteInclRoma'])
print("Correlation between % Non-White (incl. Roma) and Y_true:", correlation)

r_value, p_value = pearsonr(merged_df['y_true'], merged_df['PctNonWhiteInclRoma'])

print(f"Pearson correlation coefficient: {r_value}")
print(f"P-value: {p_value}")

# Optional: interpret
if p_value < 0.05:
    print("✅ Statistically significant correlation (p < 0.05)")
else:
    print("⚠️ Correlation is NOT statistically significant (p ≥ 0.05)")


print(f"Pearson r (y_true vs. % Black): {r_black}")
print(f"P-value: {p_black}")

if p_black < 0.05:
    print("✅ Statistically significant correlation")
else:
    print("⚠️ Not statistically significant")


merged_df = pd.merge(
    filtred_features_grouped,  # has 'LSOA code' and 'y_true'
    ethnicity_percentages_df, # has 'LSOA_code' and ethnicity %
    left_on='LSOA_code',
    right_on='LSOA_code',
    how='inner'
)

cols_to_check = [
    "PctNonWhiteInclRoma",
    "PctBlack",
    "PctWhite",
    "PctAsianSubcontinent",
    "PctAsianOther",
    "PctArab"
]

correlation_results = []
for col in cols_to_check:
    corr, p_value = pearsonr(merged_df["y_true"], merged_df[col])
    correlation_results.append({
        "EthnicityGroup": col,
        "CorrelationWithYTrue": corr,
        "PValue": p_value
    })

correlation_df = pd.DataFrame(correlation_results)

correlation_df.to_excel("correlation_ethnicity_ytrue.xlsx", index=False)