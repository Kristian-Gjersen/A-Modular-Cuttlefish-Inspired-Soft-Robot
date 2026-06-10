import nidaqmx
from nidaqmx.constants import AcquisitionType
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import os
import socket

#Measures for converting voltage into Force (N)
LOAD_CELL_CAPACITY_LBF = 5.0
LBF_TO_N = 4.4482216152605
LOAD_CELL_CAPACITY_N = LOAD_CELL_CAPACITY_LBF * LBF_TO_N

EXCITATION_V = 5.0
RATED_OUTPUT_MV_V = 2.0
ZERO_VOLTAGE = 0.0

DISTANCE_TO_SENSOR = 5
DISTANCE_TO_ROBOT = 50

FULL_SCALE_OUTPUT_V = 5 #(RATED_OUTPUT_MV_V / 1000) * EXCITATION_V

def voltage_to_force(voltage):
    return (voltage - ZERO_VOLTAGE) / (FULL_SCALE_OUTPUT_V - ZERO_VOLTAGE) * LOAD_CELL_CAPACITY_N * (DISTANCE_TO_SENSOR/DISTANCE_TO_ROBOT)



#USER SETTINGS
#=============

#DAQ 
DAQ_DEVICE = "Dev1"
DAQ_CHANNEL = "ai0"
SAMPLE_RATE = 1000  #Hz
CHUNK_SIZE = 100 #samples per read

#Arduino
ARDUINO_PORT = "COM3"
BAUD_RATE = 115200

CMD_GO = "go\n"
DONE_KEYWORD = "done"

MAX_WAIT_TIME = 200  #seconds
EXPERIMENT_TIME = 10000 #Miliseconds

#ESP motor controller
ESP_IP = "10.28.145.53"
ESP_PORT = 80

#Experiment parameters
frequencies = [50, 75, 100] # <- duty cycle

REPETITIONS = 6

#Save location
SAVE_ROOT = r"Tracking Results\Daq records\Purple Fin" #<-- Change Folder Depending on the test made

#INITIALIZE ARDUINO
#==================

print("Connecting to Arduino...")
arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

#Flush startup messages
while arduino.in_waiting:
    print("Arduino:", arduino.readline().decode().strip())


#INITIALIZE ESP
#==============

print("Connecting to ESP...")
esp = socket.socket()
esp.connect((ESP_IP, ESP_PORT))

def send_esp(cmd):
    try:
        esp.sendall((cmd + "\n").encode())
    except Exception as e:
        print("ESP socket error:", e)

send_esp("STOP")


#INITIALIZE DAQ
#==============

print("Setting up DAQ...")
task = nidaqmx.Task()
task.ai_channels.add_ai_voltage_chan(f"{DAQ_DEVICE}/{DAQ_CHANNEL}")
task.timing.cfg_samp_clk_timing(
    rate=SAMPLE_RATE,
    sample_mode=AcquisitionType.CONTINUOUS
)


#EXPERIMENT LOOP
#===============

for freq in frequencies:

    print(f"\n=== Running: {freq} Hz")

    #Set motor duty cycle on ESP
    send_esp(f"DRIVE:{freq}")
    time.sleep(2)

    #Flush Arduino buffer
    while arduino.in_waiting:
        print("Arduino:", arduino.readline().decode().strip())

    #Plot setup
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))

    for rep in range(REPETITIONS):

        print(f"\nStarting experiment {rep+1}...")

        data = []
        timestamps = []

        arduino.write(f"t {EXPERIMENT_TIME}\n".encode())
        time.sleep(0.1)

        #Start DAQ
        task.start()
        send_esp(f"DRIVE:{freq}")
        print("Sending to esp: " + freq)
        arduino.write(CMD_GO.encode())

        t0 = time.time()
        done = False

        while not done:

            #Read from DAQ
            samples = task.read(number_of_samples_per_channel=CHUNK_SIZE)

            samples = np.array(samples)

            #Create timestamps
            n = len(samples)
            start_index = len(data)
            t_chunk = (start_index + np.arange(n)) / SAMPLE_RATE

            data.extend(samples)
            timestamps.extend(t_chunk)

            #Check Arduino for "done"
            if arduino.in_waiting:
                line = arduino.readline().decode().strip()
                if DONE_KEYWORD in line:
                    print("Arduino:", line)
                    done = True

            #Timeout safety
            if time.time() - t0 > MAX_WAIT_TIME:
                print("WARNING: Timeout waiting for Arduino")
                break

        send_esp("STOP")
        task.stop()
        time.sleep(2)
        

        #Convert to numpy
        t = np.array(timestamps)
        voltage = np.array(data)
        force = voltage_to_force(voltage)

        
        #SAVE CSV
        #========

        folder = os.path.join(
            SAVE_ROOT,
            f"{freq}Hz",
        )
        os.makedirs(folder, exist_ok=True)

        filename = os.path.join(folder, f"exp_{rep+1}.csv")

        np.savetxt(
            filename,
            np.column_stack((t, voltage, force)),
            delimiter=",",
            header="time,voltage,force_N",
            comments=""
        )

        print(f"Saved: {filename}")

        #PLOT
        #====
        ax = axes.flatten()[rep]
        ax.plot(t, force)
        ax.set_title(f"Exp {rep+1}")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Force [N]")
        ax.grid(True)

    plt.suptitle(f"Duty cycle {freq}")
    plt.tight_layout()
    plt.show()

print("\nAll experiments completed!")

#Cleanup
task.close()
arduino.close()
esp.close()