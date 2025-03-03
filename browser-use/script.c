#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_TASK_LENGTH 1024

// Function to process a task and return status
int process_task(const char* task) {
    // This function takes a task string as input and executes it using the Python script
    
    // Create a buffer for the shell command with extra space for the Python command
    char command[MAX_TASK_LENGTH + 50];  // +50 for command syntax and file path
    
    // Format the shell command that will:
    // 1. Use echo to output the task
    // 2. Pipe (|) it to ls -al
    // 3. Redirect the output to output.txt
    snprintf(command, sizeof(command), "echo \"%s\" | ls -al > output.txt", task);
    
    // Execute the shell command using system()
    // system() returns the exit status - 0 for success, non-zero for failure
    int status = system(command);
    
    // Return the status code to the caller
    return status;
}

// Optional: Keep the main function for testing
int main() {
    char task[MAX_TASK_LENGTH];

    // Get the task from user
    printf("Enter your task: ");
    fgets(task, MAX_TASK_LENGTH, stdin);

    // Remove trailing newline if present
    unsigned int len = strlen(task);
    if (len > 0 && task[len-1] == '\n') {
        task[len-1] = '\0';
    }

    // Test the process_task function
    int status = process_task(task);
    if (status != 0) {
        printf("Error executing command\n");
        return 1;
    }
    
    printf("Output has been saved to output.txt\n");
    return 0;
}

