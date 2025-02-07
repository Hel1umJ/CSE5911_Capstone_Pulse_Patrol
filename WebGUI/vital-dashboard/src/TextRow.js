import React from "react";
import './TextRow.css';

function TextRow({ title, subtitle, rev=false, large=false }) {
  return (
    <div className="text-row">
        {rev ? (
          <>
            {large ? <h4>{subtitle}</h4> : <p>{subtitle}</p>}
            <h1>{title}</h1>
          </>
        ) : (
          <>
            <h1>{title}</h1>
            {large ? <h4>{subtitle}</h4> : <p>{subtitle}</p>}
          </>
        )}
    </div>
  );
}

export default TextRow;
