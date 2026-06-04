import pandas as pd
import yaml


def split_name(name):
    parts = name.split(" ")
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    else:
        return name, ""


df = pd.read_csv("Matrimonio G&D - Invitati.csv")
guests = df.loc[df["Stato"].isin(["Parteciperà", "Dubbio"])]
names = guests[["Nome e cognome"]]
names_splitted = names["Nome e cognome"].apply(split_name)

result = [{"name": first, "surname": last} for first, last in names_splitted]

yaml_content = yaml.dump(result, allow_unicode=True, default_flow_style=False)

with open("data/guests.yaml", "w", encoding="utf-8") as file:
    file.write(yaml_content)
