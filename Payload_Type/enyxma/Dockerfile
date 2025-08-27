FROM itsafeaturemythic/mythic_python_go:latest

# Install dependencies, including mythic_container
RUN pip3 install mythic_container==0.5.25 requests

# Set the working directory inside the container
WORKDIR /Mythic/

# Copy the payload files into the container
COPY [".", "."]

# Run the agent
CMD ["python3", "main.py"]