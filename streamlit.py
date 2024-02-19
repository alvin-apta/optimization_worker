import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

def main():
    st.title('Employee Shift Scheduling App')
    st.markdown("""
    This app helps in scheduling shifts for employees across different days of the week. The objective
    is to efficiently allocate shifts to workers while meeting constraints and maximizing specific criteria.

    **Maximize:**
    - Optimal utilization of available workforce.
    - Fair distribution of shifts among employees.
    - Adjust the result using shift request

    **Constraints:**
    - Each employee can only work a certain maximum number of shifts per week and day.
    - No double shift per day.
    - One shift one worker

    ### Shift Requests
                
    """)

    total_workers = st.sidebar.number_input('Total Workers', min_value=1, value=1)
    num_shifts = st.sidebar.number_input('Number of Shifts', min_value=1, value=1)

    shift_requests = [[[0] * num_shifts for _ in range(7)] for _ in range(total_workers)] 

    # Show expandable div for each worker
    daily = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for i in range(total_workers):
            with st.expander(f'Worker {i+1}'):
                shift_columns = st.columns(7)  # Create 7 columns for each day of the week
                for day in range(7):  # Assuming shifts for 7 days in a week
                    with shift_columns[day]:
                        st.write(daily[day])
                        for shift in range(1, num_shifts + 1):
                            shift_requests[i][day][shift-1] = st.checkbox(f'Shift {shift}', key=f'{i+1}_{day}_{shift}')

    if st.button('Run Module',type="primary"):
        # Run your module here
        df = run_schedule(total_workers,num_shifts,shift_requests)
        st.write('Module executed successfully!')
        st.write(df, index=False)

    # # Show result dataframe in a table
    # st.subheader('Result Schedule')
    # st.write(schedule_df)

def run_schedule(total_workers,num_shifts,shift_requests):
    """worker scheduling problem with shift requests."""

    # This program tries to find an optimal assignment of workers to shifts
    # (3 shifts per day, for 7 days), subject to some constraints (see below).
    # Each worker can request to be assigned to specific shifts.
    # The optimal assignment maximizes the number of fulfilled shift requests.
    
    num_workers = total_workers
    num_shifts = num_shifts
    num_days = 7
    all_workers = range(num_workers)
    all_shifts = range(num_shifts)
    all_days = range(num_days)


    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: worker 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_workers:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")

    # Each shift is assigned to exactly one worker in .
    for d in all_days:
        for s in all_shifts:
            model.AddExactlyOne(shifts[(n, d, s)] for n in all_workers)

    # Each worker works at most one shift per day.
    for n in all_workers:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

    # Try to distribute the shifts evenly, so that each worker works
    # min_shifts_per_worker shifts. If this is not possible, because the total
    # number of shifts is not divisible by the number of workers, some workers will
    # be assigned one more shift.
    min_shifts_per_worker = (num_shifts * num_days) // num_workers
    if num_shifts * num_days % num_workers == 0:
        max_shifts_per_worker = min_shifts_per_worker
    else:
        max_shifts_per_worker = min_shifts_per_worker + 1
    for n in all_workers:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        model.Add(min_shifts_per_worker <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_worker)

    # pylint: disable=g-complex-comprehension
    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_workers
            for d in all_days
            for s in all_shifts
        )
    )

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    df = {}
    if status == cp_model.OPTIMAL:
        print("Solution:")
        for d in all_days:
            df[d]={}
            print("Day", d)
            for n in all_workers:
                for s in all_shifts:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        if shift_requests[n][d][s] == 1:
                            print("worker", n, "works shift", s, "(requested).")
                        else:
                            print("worker", n, "works shift", s, "(not requested).")
                        df[d][s]= "Worker " + str(n+1) 
                        # df[d][s]= n 
            print()
        print(
            f"Number of shift requests met = {solver.ObjectiveValue()}",
            f"(out of {num_workers * min_shifts_per_worker})",
        )
    else:
        print("No optimal solution found !")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")

    xxx = pd.DataFrame(df)
    xxx = xxx.sort_index().reset_index().rename(columns={0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun","index":"Shift"})
    xxx["Shift"] = xxx["Shift"] +1
    return xxx

if __name__ == "__main__":
    main()
