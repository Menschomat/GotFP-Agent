from google.adk.agents.llm_agent import Agent

def calculator(operation: str, a: float, b: float) -> dict:
    """Performs a basic arithmetic operation (add, subtract, multiply, divide).

    Args:
        operation: The arithmetic operation to perform (add, subtract, multiply, divide).
        a: The first number.
        b: The second number.

    Returns:
        A dictionary containing the status and result of the operation.
    """
    operation = operation.lower().strip()
    if operation == "add":
        res = a + b
    elif operation == "subtract":
        res = a - b
    elif operation == "multiply":
        res = a * b
    elif operation == "divide":
        if b == 0:
            return {"status": "error", "message": "Cannot divide by zero."}
        res = a / b
    else:
        return {"status": "error", "message": f"Unsupported operation: {operation}"}
    
    return {"status": "success", "result": res}

# Root agent definition
root_agent = Agent(
    model="gemini-2.5-flash",
    name="calculator_agent",
    description="A helpful assistant that can perform math operations using its calculator tool.",
    instruction="You are a math helper. When asked to do calculations, use the calculator tool to compute the correct answer.",
    tools=[calculator],
)
