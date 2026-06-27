function DiagnosisCard({ diagnosis }) {

    if (!diagnosis) return null;

    return (

        <div className="card">

            <h2>🧠 AI Diagnosis</h2>

            <p>
                <strong>Root Cause:</strong>
            </p>

            <p>{diagnosis.root_cause}</p>

            <br />

            <p>
                <strong>Suggested Fix:</strong>
            </p>

            <p>{diagnosis.suggested_fix}</p>

            <br />

            <p>

                <strong>Confidence:</strong>

                {" "}

                {diagnosis.confidence}

            </p>

        </div>

    );

}

export default DiagnosisCard;