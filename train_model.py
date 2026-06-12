import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor


# Load CSV
df = pd.read_csv("dataset/car_prediction_data.csv")

print(df.head())
print(df.columns)


# Separate input and output
X = df.drop("Selling_Price", axis=1)
y = df["Selling_Price"]


# Convert text columns into numbers
X = pd.get_dummies(X)


# Save feature names
features = X.columns.tolist()


# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Train model
model = RandomForestRegressor(
    n_estimators=300,
    random_state=42
)

model.fit(X_train, y_train)


# Save model
joblib.dump(model, "model.pkl")
joblib.dump(features, "features.pkl")


print("Training Completed!")
print("Model saved successfully")