from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

appliances = []

FLOORS = ["1st Floor", "2nd Floor", "Basement"]


def get_appliance_recommendations(appliance):
    name = appliance.get("name", "").lower()

    recommendations = {
        "air conditioner": {
            "hours": "Best used during the warmer parts of the day, usually late morning through evening. Try to reduce use overnight if outdoor temperatures drop.",
            "pair_with": ["Ceiling Fan", "Heater"],
            "tip": "Run with a fan to circulate cool air more efficiently."
        },
        "washing machine": {
            "hours": "Best used during off-peak daytime hours, such as late morning or early afternoon.",
            "pair_with": ["Dryer"],
            "tip": "Run loads back-to-back with the dryer to finish laundry in one cycle window."
        },
        "dryer": {
            "hours": "Best used after the washing machine finishes, preferably in one continuous laundry session.",
            "pair_with": ["Washing Machine"],
            "tip": "Using it right after the washer helps complete laundry more efficiently."
        },
        "dishwasher": {
            "hours": "Best used in the evening after meals, or later at night if you want it out of the way.",
            "pair_with": ["Water Heater"],
            "tip": "Running full loads improves efficiency."
        },
        "refrigerator": {
            "hours": "Runs continuously, but keep door openings lower during hot midday periods to reduce strain.",
            "pair_with": ["Microwave"],
            "tip": "Keep it full but not overcrowded for best cooling performance."
        },
        "microwave": {
            "hours": "Short bursts during meal prep are ideal, usually morning, lunch, or dinner.",
            "pair_with": ["Refrigerator", "Coffee Maker"],
            "tip": "Use for quick heating instead of longer oven cycles when possible."
        },
        "coffee maker": {
            "hours": "Best used in the morning or early afternoon.",
            "pair_with": ["Microwave", "Toaster"],
            "tip": "Morning kitchen tasks can be grouped together."
        },
        "oven": {
            "hours": "Best used during meal prep windows, especially late afternoon or evening.",
            "pair_with": ["Stove"],
            "tip": "Batch cooking can reduce repeated energy use."
        },
        "stove": {
            "hours": "Best used around meal times.",
            "pair_with": ["Oven"],
            "tip": "Coordinate cooking tasks to avoid reheating later."
        },
        "television": {
            "hours": "Best used during leisure hours, usually evening.",
            "pair_with": ["Gaming Console"],
            "tip": "Turn off fully instead of leaving on standby."
        },
        "heater": {
            "hours": "Best used early morning and evening when temperatures are cooler.",
            "pair_with": ["Air Conditioner"],
            "tip": "Use only when needed and keep doors/windows sealed."
        }
    }

    default_recommendation = {
        "hours": "Best used during the times of day when you need it most, while avoiding unnecessary long run times.",
        "pair_with": ["No specific pairing available"],
        "tip": "Try grouping similar tasks together to use appliances more efficiently."
    }

    return recommendations.get(name, default_recommendation)


@app.route("/")
def home():
    selected_floor = request.args.get("floor", "1st Floor")

    filtered_appliances = []
    for index, appliance in enumerate(appliances):
        if appliance.get("floor", "1st Floor") == selected_floor:
            filtered_appliances.append({
                "id": index,
                **appliance
            })

    return render_template(
        "index.html",
        appliances=filtered_appliances,
        floors=FLOORS,
        selected_floor=selected_floor
    )


@app.route("/add", methods=["GET", "POST"])
def add_appliance():
    if request.method == "POST":
        appliance_name = request.form.get("name", "").strip()
        model = request.form.get("model", "").strip()
        usage_frequency = request.form.get("usage_frequency", "").strip()
        usage_amount = request.form.get("usage_amount", "").strip()
        room = request.form.get("room", "").strip()
        floor = request.form.get("floor", "").strip()

        if appliance_name:
            appliances.append({
                "name": appliance_name,
                "model": model,
                "usage_frequency": usage_frequency,
                "usage_amount": usage_amount,
                "room": room,
                "floor": floor or "1st Floor"
            })

        return redirect(url_for("home", floor=floor or "1st Floor"))

    return render_template("add_appliance.html", floors=FLOORS)


@app.route("/edit/<int:appliance_id>", methods=["GET", "POST"])
def edit_appliance(appliance_id):
    if appliance_id < 0 or appliance_id >= len(appliances):
        return redirect(url_for("home"))

    appliance = appliances[appliance_id]

    if request.method == "POST":
        appliance["name"] = request.form.get("name", "").strip()
        appliance["model"] = request.form.get("model", "").strip()
        appliance["usage_frequency"] = request.form.get("usage_frequency", "").strip()
        appliance["usage_amount"] = request.form.get("usage_amount", "").strip()
        appliance["room"] = request.form.get("room", "").strip()
        appliance["floor"] = request.form.get("floor", "").strip() or "1st Floor"

        return redirect(url_for("home", floor=appliance["floor"]))

    return render_template(
        "edit_appliance.html",
        appliance=appliance,
        appliance_id=appliance_id,
        floors=FLOORS
    )


@app.route("/overview")
def overview():
    return render_template("overview.html", appliances=appliances)


@app.route("/overview/<int:appliance_id>")
def appliance_overview(appliance_id):
    if appliance_id < 0 or appliance_id >= len(appliances):
        return redirect(url_for("overview"))

    appliance = appliances[appliance_id]
    recommendation = get_appliance_recommendations(appliance)

    return render_template(
        "appliance_overview.html",
        appliance=appliance,
        recommendation=recommendation,
        appliance_id=appliance_id
    )


@app.route("/layout")
def layout():
    selected_floor = request.args.get("floor", "1st Floor")

    room_order = [
        "Living Room",
        "Kitchen",
        "Dining Room",
        "Hallway",
        "Bedroom",
        "Bathroom",
        "Office"
    ]

    room_appliances = {room: [] for room in room_order}
    room_appliances["Other"] = []

    filtered_appliances = [
        appliance for appliance in appliances
        if appliance.get("floor", "1st Floor") == selected_floor
    ]

    for index, appliance in enumerate(appliances):
        if appliance.get("floor", "1st Floor") != selected_floor:
            continue

        room = appliance.get("room", "").strip()
        appliance_with_id = {
            "id": index,
            **appliance
        }

        if room in room_appliances:
            room_appliances[room].append(appliance_with_id)
        else:
            room_appliances["Other"].append(appliance_with_id)

    return render_template(
        "layout.html",
        room_appliances=room_appliances,
        floors=FLOORS,
        selected_floor=selected_floor,
        appliances=filtered_appliances
    )


@app.route("/profile")
def profile():
    return render_template("profile.html")


if __name__ == "__main__":
    app.run(debug=True)
