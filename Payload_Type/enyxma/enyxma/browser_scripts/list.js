function(task, responses) {
    // If the task errored, just dump the raw text
    if (task.status.includes("error")) {
        return { plaintext: responses.join("") };
    }
    // If the task completed and we have output, try to parse it
    else if (task.completed && responses.length > 0) {
        // Combine all chunks into one text blob
        const text = responses.join("");
        const lines = text.split("\n").filter(line => line.trim().length > 0);

        // If there aren’t at least a title + header + one row, fall back to plaintext
        if (lines.length < 3) {
            return { plaintext: text };
        }

        // First line is the absolute path (“Listing contents of: /real/path”)
        const title = lines[0].replace(/^Listing contents of:\s*/, "");

        // Second line are the column names (tab‑separated)
        const cols = lines[1].split("\t").filter(Boolean);

        // Define default widths and types per column
        const widthMap = {
            UID:   80,
            GID:   80,
            Size: 100,
            MTime: 200,
            Name:  null  // let Name expand to fill remaining space
        };

        const headers = cols.map(col => {
            // choose cell type
            let type = "string";
            if (col === "Size") type = "size";

            const header = { plaintext: col, type };

            // make “Name” fill the rest of the width
            if (col === "Name") {
                header.fillWidth = true;
            }
            // otherwise assign a fixed width if present
            else if (widthMap[col]) {
                header.width = widthMap[col];
            }

            return header;
        });

        // Build each row object
        const rows = [];
        for (let i = 2; i < lines.length; i++) {
            const fields = lines[i].split("\t");
            const row = {};
            for (let j = 0; j < cols.length; j++) {
                row[cols[j]] = { plaintext: fields[j] || "" };
            }
            rows.push(row);
        }

        // Return the table for Mythic’s new UI
        return {
            table: [{
                title,
                headers,
                rows
            }]
        };
    }
    // If not yet finished, notify the user
    else {
        return { plaintext: "Listing in progress…" };
    }
}