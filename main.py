import streamlit as st
import requests
import pandas as pd
from geopy.distance import geodesic as gd
import os

can_calculate = False

TOLERANCE = 10

def get_coords(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place,
              "format": "json"}
    headers = {"User-Agent": "School-Project"}
    response = requests.get(url, params = params, headers=headers)
    results = response.json()

    if not results: return None

    data = results[0]
    lat = data["lat"]
    lon = data["lon"]
    bbox = data["boundingbox"]
    height = float(bbox[1]) - float(bbox[0])
    width = float(bbox[3]) - float(bbox[2])
    marker_radius = min(((height + width) / 2) * (10 ** 5),     (10 ** 6))

    return(place, float(lat), float(lon), float(marker_radius))

def get_distance(coords_1: list[float], coords_2: list[float]) -> float:
    x1, y1 = coords_1
    x2, y2 = coords_2
    distance_degrees = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
    distance_km = distance_degrees * 111
    return distance_km

def check_collinear(p1, p2, p3):

    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    area = abs(
        x1*(y2-y3) +
        x2*(y3-y1) +
        x3*(y1-y2)
    ) / 2

    return area

def investigate(place1_index: int, place2_index: int, inv_num: int) -> list[float]:
    estimate_point_1 = (data.loc[place1_index, "lon"], data.loc[place1_index, "lat"])
    estimate_point_2 = (data.loc[place2_index, "lon"], data.loc[place2_index, "lat"])

    real_point_1 = (data.loc[place1_index, "lat"], data.loc[place1_index, "lon"])
    real_point_2 = (data.loc[place2_index, "lat"], data.loc[place2_index, "lon"])

    st.divider()
    st.subheader(f"_Investigation {inv_num}:_ {data.loc[place1_index, 'name']} and {data.loc[place2_index, 'name']}")
    st.write("When we use the latitudes and longitudes of these places as x and y values, we can use the distance formula,")
    st.latex("\\boxed{d = \sqrt{(x_{2} - x_{1})^2 + (y_{2} - y_{1})^2}},")
    st.write("then we can calculate the distance between the places!")
    st.write(
        f"The result of that operation is: :red[{(estimate := get_distance(
            estimate_point_1, estimate_point_2
            ))}km]"
        )
    st.write(":orange[But this does not account for the Earth's curvature. Hence, this is only an estimate.]")
    real = gd(real_point_1, real_point_2).km
    st.write(
        f"Accounting for the curvature, an online tool tells us "
        f"that the distance is :violet[{real} km]"
    )
    st.write("So,")
    st.latex(f"d_{{real}} = {real}")
    st.latex(f"d_{{estimate}} = {estimate}")
    st.latex(f"\\boxed{{Error = d_{{real}} - d_{{estimate}} = {real - estimate}}}")    
    st.space("medium")
    _, col2, _ = st.columns([1, 3, 1], vertical_alignment="bottom")
    with col2:
        col2.bar_chart(data = (bar_df := pd.DataFrame(
            {
                "Type": ["Estimated", "Real"],
                "Distances": [estimate, real]
            }
        )), x = "Type", y = "Distances", width="stretch")
    
    int_point_1 = tuple(int(point) for point in estimate_point_1)
    int_point_2 = tuple(int(point) for point in estimate_point_2)
    return [int_point_1, int_point_2, estimate, real]

st.title("_Collinearity on Earth: Test it out!_")

with st.form("get_places"): 
    st.header("Enter the places you would like to check")

    place1 = st.text_input("Place 1: ")
    place2 = st.text_input("Place 2: ")
    place3 = st.text_input("Place 3: ")

    submitted = st.form_submit_button("Submit")

st.divider()

if submitted:

    try:
        data = pd.DataFrame(
            data = [get_coords(place1) , get_coords(place2), get_coords(place3)],
            columns=["name", "lat", "lon", "size"]
        )
        my_map = st.map(data, size = "size")
        can_calculate = True

    except Exception:
        st.header("Sorry, you place wasnt found :/")
        st.write("Maybe try something else?")

if can_calculate:
    compare_tupple1 = investigate(0, 1, 1)
    compare_tuple2 = investigate(1, 2, 2)
    compare_tuple3 = investigate(0, 2, 3)

    compare_tupple1.append(f"{data.loc[0, 'name']}, and {data.loc[1, 'name']}")
    compare_tuple2.append(f"{data.loc[1, 'name']}, and {data.loc[2, 'name']}")
    compare_tuple3.append(f"{data.loc[0, 'name']}, and {data.loc[2, 'name']}")

    retrieve_points = lambda idx: (data.loc[idx, "lon"], data.loc[idx, "lat"])
    p1, p2, p3 = (retrieve_points(i) for i in range(0, 3))

    st.divider()
    st.header("_The million-dollar question_: Are they collinear?")
    st.write("Three collinear points always form a :yellow[triangle with area 0]. We can use that logic to identify collinearity of points")
    st.write("The formula,  ")
    st.latex(r"\boxed{\text{Area} = \frac{1}{2}\left|x_1(y_2-y_3)+x_2(y_3-y_1)+x_3(y_1-y_2)\right|}")
    st.write("gives us the area estimate of any three points on a plane.")
    st.write(f"Substituting our :green[longitude and latitude values as x and y], we get :rainbow[{(a := check_collinear(p1, p2, p3))} sq. coordinate degrees]")
    with st.container(border=True):
        if a < TOLERANCE:
            st.write("As this value is pretty close to zero, considering measurement errors and the huge distances we're dealing with, we can say that the places are collinear")
        else:
            st.write("This value is too big to be considered collinear. Hence we can say that the places are not collinear!")

    st.divider()
    chart_container = st.container(width = "stretch", height = 450, horizontal_alignment="center")
    chart_container.subheader("Coordinates plotted on graph", text_alignment="center")
    chart_container.line_chart(data = data, x = "lon", y = "lat", x_label = "Longitude", y_label = "Latitude")

    distance_df = pd.DataFrame(
        (compare_tupple1, compare_tuple2, compare_tuple3),
        columns=["Coordinates of place 1", "Coordinates of place 2", "Estimated Distance", "Real Distance", "Places being compared"]
    )
    distance_df.to_excel((path := os.path.join(os.getcwd(), "data.xlsx")), index = False)
    
    st.divider()
    st.subheader("Excel sheet data: ")
    st.dataframe(distance_df)
    with open("data.xlsx", "rb") as file:
        st.download_button(
            label="Download",
            data=file,
            file_name="data.xlsx",
            on_click="ignore",
            icon=":material/download:", 
        )