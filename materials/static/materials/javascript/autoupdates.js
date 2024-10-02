// autoupdates.js

function handleFileSelect() {
    const fileInput = document.querySelector('[name="inputRISFile"]');

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = function (event) {
            const fileContent = event.target.result;
            const lines = fileContent.split('\n'); // Split content into lines

            // Initialize variables to store extracted data
            let title = '';
            let journal = '';
            let volume = '';
            let pages_start = '';
            let pages_end = '';
            let year = '';
            let doi = '';
            let isbn = '';
            let authors = [];

            // Iterate over lines and extract data
            lines.forEach(line => {
                line = line.trim(); // Remove leading/trailing whitespace
                if (line.startsWith('TI  -') || line.startsWith('T1  -')) {
                    title += line.replace(/^(T1|TI)\s*-\s*/, '') + ' ';
                }
                else if (line.startsWith('JO  -') || line.startsWith('JF  -')) {
                    journal += line.replace(/^(JO|JF)\s*-\s*/, '') + ' ';
                }
                else if (line.startsWith('VL  -')) {
                    volume += line.replace(/^VL\s*-\s*/, '');
                }
                else if (line.startsWith('SP  -')) {
                    pages_start += line.replace(/^SP\s*-\s*/, '');
                }
                else if (line.startsWith('EP  -')) {
                    pages_end += line.replace(/^EP\s*-\s*/, '');
                }
                else if (line.startsWith('PY  -')) {
                    year += line.replace(/^PY\s*-\s*/, '');
                }
                else if (line.startsWith('DO  -')) {
                    doi += line.replace(/^DO\s*-\s*/, '').trim();
                }
                else if (line.startsWith('SN  -')) {
                    isbn += line.replace(/^SN\s*-\s*/, '').trim();
                }
                else if (line.startsWith('AU  -')) {
                    authors.push(line.replace(/^AU\s*-\s*/, '').trim()); // Collect all authors
                }
            });

            // Now set the values of the form inputs
            const titleInput = document.querySelector('[name="title"]');
            if (titleInput) {
                titleInput.value = title.trim();
            }
            const journalInput = document.querySelector('[name="journal"]');
            if (journalInput) {
                journalInput.value = journal.trim();
            }
            const volumeInput = document.querySelector('[name="vol"]');
            if (volumeInput) {
                volumeInput.value = volume.trim();
            }
            const pagesStartInput = document.querySelector('[name="pages_start"]');
            if (pagesStartInput) {
                pagesStartInput.value = pages_start.trim();
            }
            const pagesEndInput = document.querySelector('[name="pages_end"]');
            if (pagesEndInput) {
                pagesEndInput.value = pages_end.trim();
            }
            const yearInput = document.querySelector('[name="year"]');
            if (yearInput) {
                yearInput.value = year.trim();
            }

            const doiIsbnInput = document.querySelector('[name="doi_isbn"]');
            if (doiIsbnInput) {
                if (doi && isbn) {
                    doiIsbnInput.value = doi + ', ' + isbn;
                } else {
                    doiIsbnInput.value = doi || isbn;
                }
            }

            const addAuthorButton = document.querySelector('#add-more-authors-btn'); // Button to add more authors

            // Fill authors one by one
            authors.forEach((author, index) => {
                if (index > 0) {
                    // Click the "Add more authors" button for additional authors
                    addAuthorButton.click();
                }

                const authorParts = author.split(', ');
                const lastName = authorParts[0];
                const firstName = authorParts.length > 1 ? authorParts[1] : '';

                // Populate the respective author fields dynamically
                const firstNameField = document.querySelector(`[name="first-name-${index + 1}"]`);
                const lastNameField = document.querySelector(`[name="last-name-${index + 1}"]`);

                if (firstNameField && lastNameField) {
                    firstNameField.value = firstName;
                    lastNameField.value = lastName;
                }
            });
        };

        reader.readAsText(file); // Read the file as text
    }
}

// Attach the function to the input file change event
document.querySelector('[name="inputRISFile"]').addEventListener('change', handleFileSelect);
