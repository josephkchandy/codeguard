function SummaryCard({ summary }) {

    if (!summary) return null;

    return (
        <div className="card">

            <h2>📁 Repository Summary</h2>

            <div className="stats">

                <div className="stat">
                    <h3>{summary.python_files}</h3>
                    <p>Python Files</p>
                </div>

                <div className="stat">
                    <h3>{summary.functions}</h3>
                    <p>Functions</p>
                </div>

                <div className="stat">
                    <h3>{summary.classes}</h3>
                    <p>Classes</p>
                </div>

            </div>

        </div>
    );

}

export default SummaryCard;