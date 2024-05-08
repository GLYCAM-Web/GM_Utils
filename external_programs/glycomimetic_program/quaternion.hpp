#ifndef QUATERNION_HPP
#define QUATERNION_HPP

#include "includes/GeometryTopology/coordinate.hpp"

#include <cmath>

class Quaternion{
public:
    Quaternion(double w, double x, double y, double z){
        this->w_ = w;
        this->x_ = x;
        this->y_ = y;
        this->z_ = z;
    }
    Quaternion(double w, GeometryTopology::Coordinate* coord){
        this->w_ = w;
        this->x_ = coord->GetX();
        this->y_ = coord->GetY();
        this->z_ = coord->GetZ();
    }
    Quaternion(double w, GeometryTopology::Coordinate& coord){
        this->w_ = w;
        this->x_ = coord.GetX();
        this->y_ = coord.GetY();
        this->z_ = coord.GetZ();
    }

    void Normalize(){
        double current_length = std::sqrt(w_* w_ + x_* x_ + y_* y_ + z_* z_);
        this->w_ /= current_length; 
        this->x_ /= current_length; 
        this->y_ /= current_length; 
        this->z_ /= current_length; 
    }

    void operator*(Quaternion* q){
        //q1*q2 != q2*q1. Define q as 2, this object as 1. 
        double w2 = q->GetW(), x2 = q->GetX(), y2 = q->GetY(), z2 = q->GetZ();
        const double& w1 = this->w_, x1 = this->x_, y1 = this->y_, z1 =this->z_;
        double new_w = w1*w2 - x1*x2 - y1*y2 - z1*z2;
        double new_x = w1*x2 + x1*w2 + y1*z2 - z1*y2;
        double new_y = w1*y2 - x1*z2 + y1*w2 + z1*x2;
        double new_z = w1*z2 + x1*y2 - y1*x2 + z1*w2;

        this->w_ = new_w;
        this->x_ = new_x;
        this->y_ = new_y;
        this->z_ = new_z;


/*(Q1 * Q2).w = (w1w2 - x1x2 - y1y2 - z1z2)
(Q1 * Q2).x = (w1x2 + x1w2 + y1z2 - z1y2)
(Q1 * Q2).y = (w1y2 - x1z2 + y1w2 + z1x2)
(Q1 * Q2).z = (w1z2 + x1y2 - y1x2 + z1w2*/

    }

    void operator*(Quaternion& q){
        //q1*q2 != q2*q1. Define q as 2, this object as 1.
        double w2 = q.GetW(), x2 = q.GetX(), y2 = q.GetY(), z2 = q.GetZ();
        const double& w1 = this->w_, x1 = this->x_, y1 = this->y_, z1 =this->z_;
        double new_w = w1*w2 - x1*x2 - y1*y2 - z1*z2;
        double new_x = w1*x2 + x1*w2 + y1*z2 - z1*y2;
        double new_y = w1*y2 - x1*z2 + y1*w2 + z1*x2;
        double new_z = w1*z2 + x1*y2 - y1*x2 + z1*w2;

        this->w_ = new_w;
        this->x_ = new_x;
        this->y_ = new_y;
        this->z_ = new_z;


/*(Q1 * Q2).w = (w1w2 - x1x2 - y1y2 - z1z2)
(Q1 * Q2).x = (w1x2 + x1w2 + y1z2 - z1y2)
(Q1 * Q2).y = (w1y2 - x1z2 + y1w2 + z1x2)
(Q1 * Q2).z = (w1z2 + x1y2 - y1x2 + z1w2*/

    }

    void operator*(Quaternion& q){
        double qw = q.GetW(), qx = q.GetX(), qy = q.GetY(), qz = q.GetZ();
    }



    //ACCESSOR
    double GetW(){
        return this->w_;
    }
    double GetX(){
        return this->x_;
    }
    double GetY(){
        return this->y_;
    }
    double GetZ(){
        return this->z_;
    }

    //MUTATOR
    void SetW(double w){
        this->w_ = w;
    }
    void SetX(double x){
        this->x_ = x;
    }
    void SetY(double y){
        this->y_ = y;
    }
    void SetZ(double z){
        this->z_ = z;
    }



private:
    double w_ = 0; 
    double x_ = 0; 
    double y_ = 0; 
    double z_ = 0;

}

#endif
