import { useState } from "react";

function UploadForm({ onAnalyze }) {

    const [repository, setRepository] = useState(null);
    const [bugReport, setBugReport] = useState("");

    const submit = (e) => {
        e.preventDefault();

        if (!repository) {
            alert("Please upload a ZIP file.");
            return;
        }

        onAnalyze(repository, bugReport);
    };

    return (
        <div className="card">

            <h2>📤 Upload Repository</h2>

            <form onSubmit={submit}>

                <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setRepository(e.target.files[0])}
                />

                <textarea
                    placeholder="Describe the bug..."
                    rows="5"
                    value={bugReport}
                    onChange={(e) => setBugReport(e.target.value)}
                />

                <button type="submit">
                    Analyze Repository
                </button>

            </form>

        </div>
    );
}

export default UploadForm;