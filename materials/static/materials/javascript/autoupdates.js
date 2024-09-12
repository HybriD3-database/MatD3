function handleFileSelect() {
    const fileInput = document.querySelector('[name="inputRISFile"]');
    const textInput = document.querySelector('[name="title"]');
  
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = function (event) {
            const fileContent = event.target.result;
            const lines = fileContent.split('\n'); // Split content into lines

            // Search for lines starting with "T1  -" or "TI  -"
            const relevantLines = lines.filter(line =>
                line.trim().startsWith("TI  -") || line.trim().startsWith("T1  -")
            );

            // Extract the text after "T1  -" or "T1  -"
            const extractedText = relevantLines.map(line =>
                line.trim().replace(/^(T1|TI)  -/, "")
            ).join("\n");

            // Set the extracted text to textInput.value
            textInput.value = extractedText;
        };

        reader.readAsText(file); // Read the file as text
    }
  }