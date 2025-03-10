import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { ReactiveFormsModule } from '@angular/forms';
import { MaggicCalculatorComponent } from './maggik.component';

const routes: Routes = [
  { path: "", component: MaggicCalculatorComponent }
];

@NgModule({
  declarations: [
    MaggicCalculatorComponent
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    TranslateModule.forChild(),
    ButtonModule,
    InputTextModule,
    DropdownModule,
    ReactiveFormsModule
  ]
})
export class MaggikModule { }
