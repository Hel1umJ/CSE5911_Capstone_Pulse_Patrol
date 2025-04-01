#define BUFFER_SIZE 80  // Set the number of data points 

float buffer[BUFFER_SIZE];

float sensorPin = A0; 
int Led = 7; // Single pin to go between 

float IRdat[BUFFER_SIZE];
float REDdat[BUFFER_SIZE];

float IRtemp = 0;
float REDtemp = 0;

float SpO2;

// Separate head, tail, and count for RED and IR streams
int RED_head = 0, RED_tail = 0, RED_count = 0;
int IR_head = 0, IR_tail = 0, IR_count = 0;

void findMinMax(float *data, int *head, int *tail, int *count, float &minVal, float &maxVal) {
    if (*count == 0) return;
    minVal = 5000;  // Change to a high value for testing
    maxVal = 0;  // Set to 0 for initial comparison

    for (int i = 0; i < *count; i++) {
        int idx = (*tail + i) % BUFFER_SIZE;
        if (data[idx] < minVal) minVal = data[idx];
        if (data[idx] > maxVal) maxVal = data[idx];
    }
}

float movingAverage(float *data, int *head, int *count, int windowSize) {
    if (*count == 0) return 0;
    float sum = 0;
    int validSamples = (*count < windowSize) ? *count : windowSize;
    for (int i = 0; i < validSamples; i++) {
        int idx = (*head - 1 - i + BUFFER_SIZE) % BUFFER_SIZE;
        sum += data[idx];
    }
    return sum / validSamples;
}

void push(float value, float *buffer, int *head, int *tail, int *count) {
    if (*count == BUFFER_SIZE) {
        *tail = (*tail + 1) % BUFFER_SIZE;
    } else {
        (*count)++;
    }
    buffer[*head] = value;
    *head = (*head + 1) % BUFFER_SIZE;
}

void setup() {
   Serial.begin(9600);
   Serial.flush();
   pinMode(sensorPin, INPUT);
   pinMode(Led, OUTPUT);

   // turn led to OFF state
   digitalWrite(Led, LOW);
}

void loop () {
    digitalWrite(Led, HIGH);
    REDtemp = analogRead(sensorPin);
    delay(50);
    push(REDtemp, REDdat, &RED_head, &RED_tail, &RED_count);  // For RED data
    
    digitalWrite(Led, LOW);

    
    IRtemp = analogRead(sensorPin);
    delay(50);
    push(IRtemp, IRdat, &IR_head, &IR_tail, &IR_count);  // For IR data
    

    float minIR, maxIR, minRED, maxRED;
    float smoothedIR = movingAverage(IRdat, &IR_head, &IR_count, 15);
    float smoothedRED = movingAverage(REDdat, &RED_head, &RED_count, 15);

    findMinMax(IRdat, &IR_head, &IR_tail, &IR_count, minIR, maxIR);
    findMinMax(REDdat, &RED_head, &RED_tail, &RED_count, minRED, maxRED); 
    
    //Serial.print("Min IR: "); Serial.print(minIR);
    //Serial.print(" Max IR : "); Serial.print(maxIR);
    //Serial.print(" Min RED: "); Serial.print(minRED);
    //Serial.print(" Max RED: "); Serial.println(maxRED);
    
    //Serial.print(" Smoothed IR: "); Serial.print(smoothedIR);
    //Serial.print(" Smoothed RED: "); Serial.println(smoothedRED);

    float R = ((maxRED - minRED)/(smoothedRED))/((maxIR-minIR)/(smoothedIR));
    SpO2 =110 -25*R;
    Serial.print("SpO2: "); Serial.println(SpO2);
}
