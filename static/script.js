function getBMIColor(hasil_prediksi) {
    switch (hasil_prediksi.toLowerCase()) {
      case "underweight":
        return "bmi-underweight";
      case "normal":
        return "bmi-normal";
      case "overweight":
        return "bmi-overweight";
      case "obese":
        return "bmi-obese";
      default:
        return "bg-gray-400";
    }
}

function getBMIIcon(hasil_prediksi) {
  switch (hasil_prediksi.toLowerCase()) {
    case "underweight":
      return "fas fa-arrow-down";
    case "normal":
      return "fas fa-check-circle";
    case "overweight":
      return "fas fa-exclamation-triangle";
    case "obese":
      return "fas fa-exclamation-circle";
    default:
      return "fas fa-question-circle";
  }
}

