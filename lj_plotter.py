import pandas as pd
import matplotlib.pyplot as plt

def lj_plotter(csv_file):
    """
    A generic plotter that reads a CSV file and plots its data based on headers.
    
    Parameters:
        csv_file (str): The name of the CSV file to plot.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        data = pd.read_csv(csv_file)
        
        # Display the first few rows of the data for reference
        print("Data Preview:")
        print(data.head())
        
        # Check if the CSV has at least two columns
        if data.shape[1] < 2:
            print("Error: The CSV file must have at least two columns (one for x-axis and one for y-axis).")
            return
        
        # Display column headers to the user
        print("\nAvailable columns:")
        for i, col in enumerate(data.columns):
            print(f"{i}: {col}")
        
        # Prompt the user to select columns for the x and y axes
        x_col_index = int(input("\nEnter the column index for the x-axis: "))
        y_col_index = int(input("Enter the column index for the y-axis: "))
        
        # Get the column names based on the user's selection
        x_col = data.columns[x_col_index]
        y_col = data.columns[y_col_index]
        
        # Plot the data
        plt.figure(figsize=(10, 6))
        plt.plot(data[x_col], data[y_col], marker='o', linestyle='-', label=f"{y_col} vs {x_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.title(f"{y_col} vs {x_col}")
        plt.legend()
        plt.grid(True)
        plt.show()
    
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    csv_file = input("Enter the name of the CSV file (with extension): ")
    lj_plotter(csv_file)