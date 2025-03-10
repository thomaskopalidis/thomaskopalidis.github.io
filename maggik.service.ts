import { Injectable } from '@angular/core';

export interface MaggicRiskModel {
  age: any;
  ef: any;
  sBP: any;
  BMI: any;
  creatinine: any;
  nyha: any;
  gender: any;
  smoker: any;
  diabetes: any;
  copd: any;
  hf: any;
  blocker: any;
  acei: any;
}

@Injectable({
  providedIn: 'root'
})
export class MaggikService {
  caclulateMAGGICScore(data: MaggicRiskModel) {
    const {
        age,
        ef,
        sBP,
        BMI,
        creatinine,
        nyha,
        gender,
        smoker,
        diabetes,
        copd,
        hf,
        blocker,
        acei
    } = data;

    let _efr: any = 0;

    if (ef == 0 || isNaN(ef)) {
        _efr = '--';
    } else {
        _efr =
            ef < 20 ? 7 : ef < 25 ? 6 : ef < 30 ? 5 : ef < 35 ? 3 : ef < 40 ? 2 : 0;
    }

    //	now sort out the contribution
    //	associated with age in relation
    //	to the EF

    let _efar: any = 0;

    if (age < 18 || isNaN(age) || age > 110) {
        _efar = '--';
    } else if (_efr != '--') {
        _efar =
            age < 55
                ? ef < 30
                    ? 0
                    : ef < 40
                        ? 0
                        : 0
                : age < 60
                    ? ef < 30
                        ? 1
                        : ef < 40
                            ? 2
                            : 3
                    : age < 65
                        ? ef < 30
                            ? 2
                            : ef < 40
                                ? 4
                                : 5
                        : age < 70
                            ? ef < 30
                                ? 4
                                : ef < 40
                                    ? 6
                                    : 7
                            : age < 75
                                ? ef < 30
                                    ? 6
                                    : ef < 40
                                        ? 8
                                        : 9
                                : age < 80
                                    ? ef < 30
                                        ? 8
                                        : ef < 40
                                            ? 10
                                            : 12
                                    : ef < 30
                                        ? 10
                                        : ef < 40
                                            ? 13
                                            : 15;
    } else {
        _efar = '--';
    }

    let _sbpr: any = 0;

    if (ef < 1 || isNaN(ef) || ef > 95 || sBP < 50 || isNaN(sBP) || sBP > 250) {
        _sbpr = '--';
    } else {
        _sbpr =
            sBP < 110
                ? ef < 30
                    ? 5
                    : ef < 40
                        ? 3
                        : 2
                : sBP < 120
                    ? ef < 30
                        ? 4
                        : ef < 40
                            ? 2
                            : 1
                    : sBP < 130
                        ? ef < 30
                            ? 3
                            : ef < 40
                                ? 1
                                : 1
                        : sBP < 140
                            ? ef < 30
                                ? 2
                                : ef < 40
                                    ? 1
                                    : 0
                            : sBP < 150
                                ? ef < 30
                                    ? 1
                                    : 0
                                : 0;
    }

    let _bmir: any = 0;

    if (BMI < 10 || isNaN(BMI) || BMI > 50) {
        _bmir = '--';
    } else {
        _bmir = BMI < 15 ? 6 : BMI < 20 ? 5 : BMI < 25 ? 3 : BMI < 30 ? 2 : 0;
    }

    let _crtnr: any = 0;

    if (creatinine < 20 || isNaN(creatinine) || creatinine > 1400) {
        _crtnr = '--';
    } else {
        _crtnr =
            creatinine < 90
                ? 0
                : creatinine < 110
                    ? 1
                    : creatinine < 130
                        ? 2
                        : creatinine < 150
                            ? 3
                            : creatinine < 170
                                ? 4
                                : creatinine < 210
                                    ? 5
                                    : creatinine < 250
                                        ? 6
                                        : 8;
    }

    const score =
        _efr +
        _efar +
        _sbpr +
        _bmir +
        _crtnr +
        gender +
        nyha +
        smoker +
        diabetes +
        copd +
        hf +
        blocker +
        acei;

    return score;
}
calculateRisk = (r: any, ris: any) => {
    //	a lookup
    //	1 and 3 year outlooks expressed as
    //	an array of values. The integer risk
    //	score is the index (0-50)

    const risk1 = [
        0.015, 0.016, 0.018, 0.02, 0.022, 0.024, 0.027, 0.029, 0.032, 0.036,
        0.039, 0.043, 0.048, 0.052, 0.058, 0.063, 0.07, 0.077, 0.084, 0.093,
        0.102, 0.111, 0.122, 0.134, 0.147, 0.16, 0.175, 0.191, 0.209, 0.227,
        0.248, 0.269, 0.292, 0.316, 0.342, 0.369, 0.398, 0.427, 0.458, 0.49,
        0.523, 0.557, 0.591, 0.625, 0.659, 0.692, 0.725, 0.757, 0.787, 0.816,
        0.842
    ];
    const risk3 = [
        0.039, 0.043, 0.048, 0.052, 0.058, 0.063, 0.07, 0.077, 0.084, 0.092,
        0.102, 0.111, 0.122, 0.134, 0.146, 0.16, 0.175, 0.191, 0.209, 0.227,
        0.247, 0.269, 0.292, 0.316, 0.342, 0.369, 0.397, 0.427, 0.458, 0.49,
        0.523, 0.556, 0.59, 0.625, 0.658, 0.692, 0.725, 0.756, 0.787, 0.815,
        0.842, 0.866, 0.889, 0.908, 0.926, 0.941, 0.953, 0.964, 0.973, 0.98, 0.985
    ];

    return (100 * (r == 3 ? risk3[ris] : risk1[ris])).toFixed(2);
};
}
