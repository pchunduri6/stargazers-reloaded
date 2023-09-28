import pandas as pd

from evadb.catalog.catalog_type import ColumnType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe

class StringToDataframe(AbstractFunction):
    """
    Arguments:
        None

    Input Signatures:
        input_string (str) : A string containing structured data.

    Output Signatures:
        output_dataframe (DataFrame) : A DataFrame containing structured data.

    Example Usage:
        You can use this function to convert a structured string into a DataFrame.

        input_string = "Name: John\nAge: 30\nCountry: USA"
    """

    @property
    def name(self) -> str:
        return "StringToDataframe"

    @setup(cacheable=False)
    def setup(self) -> None:
        # Any setup or initialization can be done here if needed
        pass

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["extracted_text"],
                column_types=[ColumnType.TEXT],
                column_shapes=[(None,)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["name", "country", "city", "email",
                         "occupation",
                         "programming_languages", 
                         "topics_of_interest", 
                         "social_media"],
                column_types=[ColumnType.TEXT, ColumnType.TEXT, ColumnType.TEXT, ColumnType.TEXT, ColumnType. TEXT, ColumnType.TEXT, ColumnType.TEXT, ColumnType.TEXT],
                column_shapes=[(None,), (None,), (None,), (None,), (None,), (None,), (None,), (None,)],
            )
        ],
    )
    def forward(self, input_df):
        # Ensure input is provided
        if input_df.empty or input_df.iloc[0] is None:
            raise ValueError("Input string must be provided.")

        # Initialize lists for columns
        keys_list = []
        values_list = []

        # Iterate over rows of the input DataFrame
        for _, row in input_df.iterrows():
            response = row["response"]

            # Split the input string into lines
            lines = response.strip().split("\n")

            # Initialize lists for columns in this row
            keys = []
            values = []

            # Parse the lines and extract key-value pairs
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    keys.append(key)
                    values.append(value)
                if len(parts) > 2:
                    key = parts[0].strip()
                    # value = parts[1].strip() + parts[2].strip()
                    value = [parts[i].strip() for i in range(1, len(parts))]
                    value = "".join(value)
                    keys.append(key)
                    values.append(value)

            keys_list.append(keys)
            values_list.append(values)

        # Create a DataFrame from the parsed data
        output_dataframe = pd.DataFrame(values_list, columns=keys_list)

        return output_dataframe