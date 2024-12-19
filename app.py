from flask import Flask, render_template, request, redirect, url_for
from pulp import LpMinimize, LpProblem, LpVariable, lpSum

app = Flask(__name__)

# Dummy supplier data (can be replaced with dynamic input if needed)
suppliers_data = {
    "HarvestHorizon": {"cost": 5.0, "quality": 7, "delivery": 2.0, "capacity": 100, "material": "Crops", "location": "LocationA"},
    # Add all suppliers here as per your original data...
}

@app.route('/')
def home():
    return render_template('index.html', suppliers_data=suppliers_data)

@app.route('/supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        supplier_name = request.form['supplier_name']
        raw_material = request.form['raw_material']
        cost = float(request.form['cost'])
        quality = float(request.form['quality'])
        delivery = float(request.form['delivery'])
        capacity = float(request.form['capacity'])
        location = request.form['location']

        # Add the supplier to suppliers_data
        suppliers_data[supplier_name] = {"cost": cost, "quality": quality, "delivery": delivery, "capacity": capacity, "material": raw_material, "location": location}
        
        return redirect(url_for('home'))
    
    return render_template('add_supplier.html')

@app.route('/customer', methods=['GET', 'POST'])
def customer():
    if request.method == 'POST':
        raw_material = request.form['raw_material']
        total_demand = float(request.form['total_demand'])
        min_quality = float(request.form['min_quality'])
        max_delivery = float(request.form['max_delivery'])

        matching_suppliers = {k: v for k, v in suppliers_data.items() if v["material"] == raw_material}

        if not matching_suppliers:
            return "No matching suppliers found for the selected raw material type."

        model, x = solve_supplier_selection(matching_suppliers, total_demand, min_quality, max_delivery)

        best_supplier = max(matching_suppliers, key=lambda i: (x[i].varValue, -x[i].varValue))
        result = {
            "best_supplier": best_supplier,
            "order_quantity": x[best_supplier].varValue,
            "cost_per_unit": matching_suppliers[best_supplier]['cost'],
            "location": matching_suppliers[best_supplier]['location'],
            "delivery_time": matching_suppliers[best_supplier]['delivery'],
            "total_cost": model.objective.value()
        }

        return render_template('customer_result.html', result=result)

    return render_template('customer_input.html')

def solve_supplier_selection(suppliers, total_demand, min_quality, max_delivery):
    model = LpProblem("Supplier_Selection", LpMinimize)
    x = {i: LpVariable(f"x_{i}", lowBound=0, upBound=suppliers[i]["capacity"]) for i in suppliers}

    model += lpSum(suppliers[i]["cost"] * x[i] for i in suppliers), "Total_Cost"
    model += lpSum(x[i] for i in suppliers) == total_demand, "Demand_Constraint"
    model += lpSum(suppliers[i]["quality"] * x[i] for i in suppliers) / total_demand >= min_quality, "Quality_Constraint"
    model += lpSum(suppliers[i]["delivery"] * x[i] for i in suppliers) / total_demand <= max_delivery, "Delivery_Constraint"
    model.solve()

    return model, x

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

