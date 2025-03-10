import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MaggikService, MaggicRiskModel } from './maggik.service';

@Component({
  selector: 'app-maggic-calculator',
  templateUrl: './maggik.component.html',
  styleUrls: ['./maggik.component.scss'],
})
export class MaggicCalculatorComponent implements OnInit {
  form!: FormGroup;
  results: any;

  constructor(private fb: FormBuilder, private maggikService: MaggikService) {}

  ngOnInit(): void {
    this.createForm();
  }

  createForm() {
    this.form = this.fb.group({
      age: ['', Validators.required],
      ejectionFraction: ['', Validators.required],
      systolicBloodPressure: ['', Validators.required],
      bmi: ['', Validators.required],
      creatinine: ['', Validators.required],
      nyhaClass: ['0', Validators.required],
      gender: ['1', Validators.required],
      activeSmoker: ['0', Validators.required],
      diabetes: ['0', Validators.required],
      copd: ['0', Validators.required],
      heartFailureFirstDiagnosed: ['2', Validators.required],
      betaBlocker: ['3', Validators.required],
      ace: ['1', Validators.required],
    });
  }

  calculate() {
    if (this.form.invalid) {
      alert('Please fill in all required fields');
      return;
    }

    const formValues = this.form.value;
    const model: MaggicRiskModel = {
      age: Number(formValues.age),
      ef: Number(formValues.ejectionFraction),
      sBP: Number(formValues.systolicBloodPressure),
      BMI: Number(formValues.bmi),
      creatinine: Number(formValues.creatinine),
      nyha: Number(formValues.nyhaClass),
      gender: Number(formValues.gender),
      smoker: Number(formValues.activeSmoker),
      diabetes: Number(formValues.diabetes),
      copd: Number(formValues.copd),
      hf: Number(formValues.heartFailureFirstDiagnosed),
      blocker: Number(formValues.betaBlocker),
      acei: Number(formValues.ace),
    };

    const score = this.maggikService.caclulateMAGGICScore(model);
    const risk1Year = this.maggikService.calculateRisk(1, score);
    const risk3Years = this.maggikService.calculateRisk(3, score);

    this.results = {
      score,
      risk1Year,
      risk3Years,
    };
  }
}
