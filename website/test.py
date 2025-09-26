import pandas as pd


def drop_first_column(input_file, output_file):
    # Load file
    df = pd.read_csv(input_file)

    # Drop first column
    df = df.iloc[:, 1:]

    # Save cleaned file
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ Cleaned file saved to {output_file}")


if __name__ == "__main__":
    drop_first_column(
        "/home/mayank/Documents/Mayank/Grad Globe Admin Panel/admin-panel/website/KC2.csv",  # input file
        "/home/mayank/Documents/Mayank/Grad Globe Admin Panel/admin-panel/website/Uni_santitized_2.csv",  # output file
    )
