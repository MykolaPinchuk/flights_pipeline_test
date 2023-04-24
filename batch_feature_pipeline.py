# feature_pipeline/feature_pipeline/helpers.py

from typing import Union, get_args, get_origin
from datetime import datetime

def map_to_avro_type(field_type):
    if field_type == str:
        return "string"
    elif field_type == bool:
        return "boolean"
    elif field_type == float:
        return "double"
    elif field_type is type(None):
        return "null"
    elif field_type == datetime:
        return {"type": "long", "logicalType": "timestamp-micros"}
    elif get_origin(field_type) == Union:
        return [map_to_avro_type(t) for t in get_args(field_type)]
    else:
        raise NotImplementedError(f"Unsupported type: {field_type}")


def named_tuple_to_avro_fields(named_tuple):
    fields = []
    for field_name, field_type in named_tuple.__annotations__.items():
        fields.append({"name": field_name, "type": map_to_avro_type(field_type)})
    return fields


csv_headers = [
    "Year",
    "Quarter",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "FlightDate",
    "Reporting_Airline",
    "DOT_ID_Reporting_Airline",
    "IATA_CODE_Reporting_Airline",
    "Tail_Number",
    "Flight_Number_Reporting_Airline",
    "OriginAirportID",
    "OriginAirportSeqID",
    "OriginCityMarketID",
    "Origin",
    "OriginCityName",
    "OriginState",
    "OriginStateFips",
    "OriginStateName",
    "OriginWac",
    "DestAirportID",
    "DestAirportSeqID",
    "DestCityMarketID",
    "Dest",
    "DestCityName",
    "DestState",
    "DestStateFips",
    "DestStateName",
    "DestWac",
    "CRSDepTime",
    "DepTime",
    "DepDelay",
    "DepDelayMinutes",
    "DepDel15",
    "DepartureDelayGroups",
    "DepTimeBlk",
    "TaxiOut",
    "WheelsOff",
    "WheelsOn",
    "TaxiIn",
    "CRSArrTime",
    "ArrTime",
    "ArrDelay",
    "ArrDelayMinutes",
    "ArrDel15",
    "ArrivalDelayGroups",
    "ArrTimeBlk",
    "Cancelled",
    "CancellationCode",
    "Diverted",
    "CRSElapsedTime",
    "ActualElapsedTime",
    "AirTime",
    "Flights",
    "Distance",
    "DistanceGroup",
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
    "FirstDepTime",
    "TotalAddGTime",
    "LongestAddGTime",
    "DivAirportLandings",
    "DivReachedDest",
    "DivActualElapsedTime",
    "DivArrDelay",
    "DivDistance",
    "Div1Airport",
    "Div1AirportID",
    "Div1AirportSeqID",
    "Div1WheelsOn",
    "Div1TotalGTime",
    "Div1LongestGTime",
    "Div1WheelsOff",
    "Div1TailNum",
    "Div2Airport",
    "Div2AirportID",
    "Div2AirportSeqID",
    "Div2WheelsOn",
    "Div2TotalGTime",
    "Div2LongestGTime",
    "Div2WheelsOff",
    "Div2TailNum",
    "Div3Airport",
    "Div3AirportID",
    "Div3AirportSeqID",
    "Div3WheelsOn",
    "Div3TotalGTime",
    "Div3LongestGTime",
    "Div3WheelsOff",
    "Div3TailNum",
    "Div4Airport",
    "Div4AirportID",
    "Div4AirportSeqID",
    "Div4WheelsOn",
    "Div4TotalGTime",
    "Div4LongestGTime",
    "Div4WheelsOff",
    "Div4TailNum",
    "Div5Airport",
    "Div5AirportID",
    "Div5AirportSeqID",
    "Div5WheelsOn",
    "Div5TotalGTime",
    "Div5LongestGTime",
    "Div5WheelsOff",
    "Div5TailNum",
]


from typing import NamedTuple, Optional
from datetime import datetime

class Flight(NamedTuple):
    timestamp: Optional[datetime]
    flight_number: str
    origin_airport_id: str
    is_cancelled: bool
    departure_delay_minutes: float
    arrival_delay_minutes: float
    taxi_out_minutes: float
    distance_miles: float


flight_avro_schema = {
    "namespace": "flight_delay_prediction",
    "type": "record",
    "name": "Flight",
    "fields": named_tuple_to_avro_fields(Flight),
}


class AirportFeatures(NamedTuple):
    timestamp: Optional[datetime]
    origin_airport_id: str
    average_departure_delay: float


airport_avro_schema = {
    "namespace": "flight_delay_prediction",
    "type": "record",
    "name": "Airport",
    "fields": named_tuple_to_avro_fields(AirportFeatures),
}


# batch_feature_pipeline.py

import argparse
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


def parse_csv(line: str):
    import csv
    return next(csv.reader([line]))


def parse_line(fields):
    from datetime import datetime
    from apache_beam.utils.timestamp import Timestamp

    data = dict(zip(csv_headers, fields))

    if (
        data["Year"] != "Year"  # skip header row
        and len(data["WheelsOff"]) == 4  #
        and len(data["FlightDate"]) == 10  # row has a flight date
        and data["Distance"] != ""
    ):
        wheels_off_hour = data["WheelsOff"][:2]
        wheels_off_minutes = data["WheelsOff"][2:]
        departure_date_time = (
            f"{data['FlightDate']}T{wheels_off_hour}:{wheels_off_minutes}:00"
        )

        cancelled = (float(data["Cancelled"]) > 0) or (float(data["Diverted"]) > 0)

        try:
            flight = Flight(
                timestamp=datetime.fromisoformat(departure_date_time),
                origin_airport_id=str(data["OriginAirportID"]),
                flight_number=f"{data['Reporting_Airline']}//{data['Flight_Number_Reporting_Airline']}",
                is_cancelled=cancelled,
                departure_delay_minutes=float(data["DepDelay"]),
                arrival_delay_minutes=float(data["ArrDelay"]),
                taxi_out_minutes=float(data["TaxiOut"]),
                distance_miles=float(data["Distance"]),
            )

            yield beam.window.TimestampedValue(
                flight, Timestamp.from_rfc3339(departure_date_time)
            )
        except:
            pass


class BuildTimestampedRecordFn(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):

        window_start = window.start.to_utc_datetime()
        return [
            AirportFeatures(
                timestamp=window_start,
                origin_airport_id=element.origin_airport_id,
                average_departure_delay=element.average_departure_delay,
            )._asdict()
        ]


class BuildTimestampedFlightRecordFn(beam.DoFn):
    def process(self, element: Flight, window=beam.DoFn.WindowParam):
        return [element._asdict()]


def run(argv=None, save_main_session=False):
    """Main entry point; defines and runs the wordcount pipeline.
    never mind default arguments, they will not be invoked."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        dest="input",
        default="/Users/simon/projects/private/gcp_mlops/data/processed/2020/2020-05.csv",
        help="Input file to process.",
    )
    parser.add_argument(
        "--output-airports",
        dest="output_airports",
        default="/Users/simon/projects/private/gcp_mlops/data/output_airports/",
        help="Output file to write results to.",
    )

    parser.add_argument(
        "--output-flights",
        dest="output_flights",
        default="/Users/simon/projects/private/gcp_mlops/data/output_flights/",
        help="Output file to write results to.",
    )

    parser.add_argument(
        "--output-read-instances",
        dest="output_read_instances",
        default="/Users/simon/projects/private/gcp_mlops/data/output_read_instances/",
        help="Output file to write results to.",
    )

    # Parse beam arguments (e.g. --runner=DirectRunner to run the pipeline locally)
    known_args, pipeline_args = parser.parse_known_args(argv)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as pipeline:
        flights = (
            pipeline
            | "read_input" >> beam.io.ReadFromText(known_args.input)
            | "parse_csv" >> beam.Map(parse_csv)
            | "create_flight_obj" >> beam.FlatMap(parse_line).with_output_types(Flight)
        )

        # Create airport data
        (
            flights
            | "window"
            >> beam.WindowInto(
                beam.window.SlidingWindows(4 * 60 * 60, 60 * 60)
            )  # 4h time windows, every 60min
            | "group_by_airport"
            >> beam.GroupBy("origin_airport_id").aggregate_field(
                "departure_delay_minutes",
                beam.combiners.MeanCombineFn(),
                "average_departure_delay",
            )
            | "add_timestamp" >> beam.ParDo(BuildTimestampedRecordFn())
            | "write_airport_data"
            >> beam.io.WriteToAvro(
                known_args.output_airports, schema=airport_avro_schema
            )
        )

        # Create flight data
        (
            flights
            | "format_output" >> beam.ParDo(BuildTimestampedFlightRecordFn())
            | "write_flight_data"
            >> beam.io.WriteToAvro(known_args.output_flights, schema=flight_avro_schema)
        )

        # Create read_instances.csv to retrieve training data from the feature store
        (
            flights
            | "format_read_instances_output"
            >> beam.Map(
                lambda flight: f"{flight.flight_number},{flight.origin_airport_id},{flight.timestamp.isoformat('T') + 'Z'}"
            )
            | "write_read_instances"
            >> beam.io.WriteToText(
                known_args.output_read_instances,
                file_name_suffix=".csv",
                num_shards=1,
                header="flight,airport,timestamp",
            )
        )