// autoupdates.js

// Function to handle RIS file parsing and field population
function handleRISFileSelect() {
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

            // Set the values of the form inputs
            document.querySelector('[name="title"]').value = title.trim();
            document.querySelector('[name="journal"]').value = journal.trim();
            document.querySelector('[name="vol"]').value = volume.trim();
            document.querySelector('[name="pages_start"]').value = pages_start.trim();
            document.querySelector('[name="pages_end"]').value = pages_end.trim();
            document.querySelector('[name="year"]').value = year.trim();
            document.querySelector('[name="doi_isbn"]').value = doi && isbn ? doi + ', ' + isbn : doi || isbn;

            const addAuthorButton = document.querySelector('#add-more-authors-btn');

            authors.forEach((author, index) => {
                if (index > 0) addAuthorButton.click();

                const authorParts = author.split(', ');
                document.querySelector(`[name="first-name-${index + 1}"]`).value = authorParts[1] || '';
                document.querySelector(`[name="last-name-${index + 1}"]`).value = authorParts[0] || '';
            });
        };

        reader.readAsText(file);
    }
}

// Function to handle BIB file parsing and field population
function handleBIBFileSelect() {
    const fileInput = document.querySelector('[name="inputBIBFile"]');

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
            let issn = '';
            let authors = [];

            // Iterate over lines and extract data from the .bib file
            lines.forEach(line => {
                line = line.trim(); // Remove leading/trailing whitespace and trailing commas
                if (line.startsWith('title =')) {
                    title = line.replace(/title\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('journal =')) {
                    journal = line.replace(/journal\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('volume =')) {
                    volume = line.replace(/volume\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('pages =')) {
                    const pages = line.replace(/pages\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                    const pagesSplit = pages.split('-'); // Split by dash for start and end pages
                    pages_start = pagesSplit[0].trim();
                    pages_end = pagesSplit.length > 1 ? pagesSplit[1].trim() : '';
                }
                else if (line.startsWith('year =')) {
                    year = line.replace(/year\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('doi =')) {
                    doi = line.replace(/doi\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('issn =')) {
                    issn = line.replace(/issn\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                }
                else if (line.startsWith('author =')) {
                    const authorString = line.replace(/author\s*=\s*[{"]/i, '').replace(/[",}]/g, '').trim();
                    authors = authorString.split(' and ').map(author => author.trim());
                }
            });

            // Now set the values of the form inputs
            document.querySelector('[name="title"]').value = title.trim();
            document.querySelector('[name="journal"]').value = journal.trim();
            document.querySelector('[name="vol"]').value = volume.trim();
            document.querySelector('[name="pages_start"]').value = pages_start.trim();
            document.querySelector('[name="pages_end"]').value = pages_end.trim();
            document.querySelector('[name="year"]').value = year.trim();
            document.querySelector('[name="doi_isbn"]').value = doi && issn ? doi + ', ' + issn : doi || issn;

            const addAuthorButton = document.querySelector('#add-more-authors-btn');

            // Populate authors and trigger the add more authors button for each subsequent author
            authors.forEach((author, index) => {
                if (index > 0) addAuthorButton.click();

                // Split the author by spaces and assume the last part is the last name
                const nameParts = author.split(' ');
                const lastName = nameParts.pop(); // The last part is the last name
                const firstName = nameParts.join(' '); // The remaining parts are the first name

                // Populate the author fields dynamically
                const firstNameField = document.querySelector(`[name="first-name-${index + 1}"]`);
                const lastNameField = document.querySelector(`[name="last-name-${index + 1}"]`);
                const institutionField = document.querySelector(`[name="institution-${index + 1}"]`);

                if (firstNameField && lastNameField && institutionField) {
                    firstNameField.value = firstName;
                    lastNameField.value = lastName;
                    institutionField.value = ''; // No institution provided in .bib
                }
            });
        };

        reader.readAsText(file); // Read the file as text
    }
}

// Attach the functions to their respective input file change events
document.querySelector('[name="inputRISFile"]').addEventListener('change', handleRISFileSelect);
document.querySelector('[name="inputBIBFile"]').addEventListener('change', handleBIBFileSelect);
