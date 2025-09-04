function highlightIssues(data, issues) {
  const highlightedData = JSON.parse(JSON.stringify(data));
  issues.forEach(issue => {
    const row = issue.row;
    const column = issue.column;
    const columnName = Object.keys(highlightedData[row])[column];
    if (highlightedData[row] && columnName) {
      highlightedData[row][columnName] = {
        value: highlightedData[row][columnName],
        issue: issue.issue_type,
        suggestion: issue.suggested_value
      };
    }
  });
  return highlightedData;
}

function applyCorrections(data, corrections) {
  const correctedData = JSON.parse(JSON.stringify(data));
  corrections.forEach(correction => {
    const row = correction.row;
    const column = correction.column;
    const columnName = Object.keys(correctedData[row])[column];
    if (correctedData[row] && columnName) {
      correctedData[row][columnName] = correction.new_value;
    }
  });
  return correctedData;
}