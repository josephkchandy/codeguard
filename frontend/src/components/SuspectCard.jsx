function SuspectCard({ suspects }) {

    if (!suspects || suspects.length === 0) return null;

    return (

        <div className="card">

            <h2>🐞 Suspicious Functions</h2>

            {suspects.map((suspect, index) => (

                <div className="suspect" key={index}>

                    <h3>{suspect.function}</h3>

                    <p>{suspect.file}</p>

                    <small>Score: {suspect.score}</small>

                </div>

            ))}

        </div>

    );

}

export default SuspectCard;