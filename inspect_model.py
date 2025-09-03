import joblib

# Apne model ka path yaha daalo
model_path = r"C:\Users\satis\Cisco Packet Tracer 8.2.2\saves\project2\diabetes_model.pkl"

print(f"🔍 Model load kar rahe hai: {model_path}")
try:
    model = joblib.load(model_path)   # yaha model memory me load hoga
    print("\n✅ Model successfully load ho gaya!")
    print("--------------------------------------------------")
    print("Model type:", type(model))   # konsa model hai, jaise DecisionTree, LogisticRegression etc.

    # Agar model ke parameters hai to print karo
    if hasattr(model, "get_params"):
        print("\n⚙️ Model Parameters:")
        for k, v in model.get_params().items():
            print(f"  {k}: {v}")

    # Agar model tree based hai to feature importance print karega
    if hasattr(model, "feature_importances_"):
        print("\n🌲 Feature Importances:")
        print(model.feature_importances_)

    # Agar linear model hai to coefficients print karega
    if hasattr(model, "coef_"):
        print("\n📊 Coefficients:")
        print(model.coef_)

    # Agar classes (0 = Non Diabetic, 1 = Diabetic) define ki hai to print karega
    if hasattr(model, "classes_"):
        print("\n🏷️ Classes:")
        print(model.classes_)

    print("\n--------------------------------------------------")
    print("ℹ️ Model inspection complete ho gaya ✅")

except Exception as e:
    print("❌ Error aaya model load karte time:", e)
